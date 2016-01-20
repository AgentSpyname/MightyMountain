import direct.directbase.DirectStart
from panda3d.core import CollisionTraverser,CollisionNode, CollisionSphere
from panda3d.core import CollisionHandlerQueue,CollisionRay
from panda3d.core import Filename,AmbientLight,DirectionalLight
from panda3d.core import PandaNode,NodePath,Camera,TextNode
from panda3d.core import Vec3,Vec4,BitMask32
from pandac.PandaModules import TransparencyAttrib
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectGui import *
from direct.actor.Actor import Actor
from direct.showbase.DirectObject import DirectObject
import random, sys, os, math
runvalue = 0


#comment
#Here are all the Formulas
itemvalue = 100
lives = 5


# width of health and stamina bars
BAR_WIDTH = 0.6
PATHFINDING = 1


# OnscreenText to hold game timer
timeText = OnscreenText(text="0", style=1, mayChange=1,
                        fg=(1,1,1,1), pos=(1.3, -0.75), scale = .05)

# Function to put instructions on the screen.
def addInstructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1,1,1,1),
                        pos=(-1.3, pos), align=TextNode.ALeft, scale = .05)

# Function to put title on the screen.
def addTitle(text):

    return OnscreenText(text=text, style=1, fg=(1,1,1,1),
                        pos=(1.3,-0.95), align=TextNode.ARight, scale = .07)

# OnscreenText to hold number of collectibles remaining 
numObjText = OnscreenText(text="10", style=1, fg=(1,1,1,1),
                          pos=(1.3, -0.60), scale = .05, mayChange=1)


# Ralph's stamina
sprintBar = OnscreenImage(image="models/sprintBar.png", 
                          pos=(0.7, 0, 0.95), scale=(BAR_WIDTH,0.2,0.2))
sprintBar.setTransparency(TransparencyAttrib.MAlpha)

def printNumObj(n):
    numObjText['text'] = (str)(n)

class World(DirectObject):

    def __init__(self):
        self.walking = Vec3()
        self.isMoving = False
        self.dest = None
        base.win.setClearColor(Vec4(0,0,0,1))


        self.keyMap = {"left":0, "right":0, "forward":0, "backward":0}
        base.win.setClearColor(Vec4(0,0,0,1))

        # here is the number of collectibles in the game
        self.numObjects = 50;
        self.rare = 1; 
        self.score = 0;


        
        # print the number of objects
        printNumObj(self.score)

        # Post the instructions
        self.title = addTitle("MightyMountain")
        self.inst1 = addInstructions(0.95, "[ESC]: Quit")
        self.inst2 = addInstructions(0.90, "[A]: Rotate Ralph Left")
        self.inst3 = addInstructions(0.85, "[D]: Rotate Ralph Right")
        self.inst4 = addInstructions(0.80, "[W]: Run Ralph Forward")
        self.inst5 = addInstructions(0.75, "[S]: Run Ralph Backward")
        self.inst6 = addInstructions(0.70, "[Space]: Run, Ralph, Run")
        
        # Set up the environment
        #
        # This environment model contains collision meshes.  If you look
        # in the egg file, you will see the following:
        #
        #    <Collide> { Polyset keep descend }
        #
        # This tag causes the following mesh to be converted to a collision
        # mesh -- a mesh which is optimized for collision, not rendering.
        # It also keeps the original mesh, so there are now two copies ---
        # one optimized for rendering, one for collisions.  

        self.environ = loader.loadModel("models/world")      
        self.environ.reparentTo(render)
        self.environ.setPos(0,0,0)
        
        # Timer to increment in the move task
        self.time = 0
        
        # Get bounds of environment
        min, max = self.environ.getTightBounds()
        self.mapSize = max-min
        
        # Create the main character, Ralph
        self.ralphStartPos = self.environ.find("**/start_point").getPos()
        self.ralph = Actor("models/ralph",
                                 {"run":"models/ralph-run",
                                  "walk":"models/ralph-walk"})
        self.ralph.reparentTo(render)
        self.ralph.setScale(.2)
        self.ralph.setPos(self.ralphStartPos)
        
        # ralph's health
        self.health = 100
        
        # ralph's stamina
        self.stamina = 100

        # Create a floater object.  We use the "floater" as a temporary
        # variable in a variety of calculations.
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)

        # Accept the control keys for movement and rotation
        self.accept("escape", sys.exit)
        
        # these don't work well in combination with the space bar
        self.accept("arrow_left", self.setKey, ["left",1])
        self.accept("arrow_right", self.setKey, ["right",1])
        self.accept("arrow_up", self.setKey, ["forward",1])
        self.accept("arrow_down", self.setKey, ["backward",1])
        self.accept("arrow_left-up", self.setKey, ["left",0])
        self.accept("arrow_right-up", self.setKey, ["right",0])
        self.accept("arrow_up-up", self.setKey, ["forward",0])
        self.accept("arrow_down-up", self.setKey, ["backward",0])
        
        self.accept("space", self.runRalph, [True])
        self.accept("space-up", self.runRalph, [False])
        
        self.accept("a", self.setKey, ["left",1])
        self.accept("d", self.setKey, ["right",1])
        self.accept("w", self.setKey, ["forward",1])
        self.accept("s", self.setKey, ["backward",1])
        self.accept("a-up", self.setKey, ["left",0])
        self.accept("d-up", self.setKey, ["right",0])
        self.accept("w-up", self.setKey, ["forward",0])
        self.accept("s-up", self.setKey, ["backward",0])

        # Game state variables
        self.isMoving = False
        self.isRunning = False

        # Set up the camera
        base.disableMouse()
        #base.camera.setPos(self.ralph.getX(),self.ralph.getY()+10,2)
        base.camera.setPos(0, 0, 0)
        base.camera.reparentTo(self.ralph)
        base.camera.setPos(0, 40, 2)
        base.camera.lookAt(self.ralph)
        
        # We will detect the height of the terrain by creating a collision
        # ray and casting it downward toward the terrain.  One ray will
        # start above ralph's head, and the other will start above the camera.
        # A ray may hit the terrain, or it may hit a rock or a tree.  If it
        # hits the terrain, we can detect the height.  If it hits anything
        # else, we rule that the move is illegal.

        base.cTrav = CollisionTraverser()

        self.ralphGroundRay = CollisionRay()
        self.ralphGroundRay.setOrigin(0,0,300)
        self.ralphGroundRay.setDirection(0,0,-1)
        self.ralphGroundCol = CollisionNode('ralphRay')
        self.ralphGroundCol.addSolid(self.ralphGroundRay)
        self.ralphGroundCol.setFromCollideMask(BitMask32.bit(0))
        self.ralphGroundCol.setIntoCollideMask(BitMask32.allOff())
        self.ralphGroundColNp = self.ralph.attachNewNode(self.ralphGroundCol)
        self.ralphGroundHandler = CollisionHandlerQueue()
        base.cTrav.addCollider(self.ralphGroundColNp, self.ralphGroundHandler)

        # camera ground collision handler
        self.camGroundRay = CollisionRay()
        self.camGroundRay.setOrigin(0,0,300)
        self.camGroundRay.setDirection(0,0,-1)
        self.camGroundCol = CollisionNode('camRay')
        self.camGroundCol.addSolid(self.camGroundRay)
        self.camGroundCol.setFromCollideMask(BitMask32.bit(0))
        self.camGroundCol.setIntoCollideMask(BitMask32.allOff())
        self.camGroundColNp = base.camera.attachNewNode(self.camGroundCol)
        self.camGroundHandler = CollisionHandlerQueue()
        base.cTrav.addCollider(self.camGroundColNp, self.camGroundHandler)

        # Place the health items
        self.placeCoins()
        
        # Place the collectibles
        self.placeCollectibles()
       
        # Uncomment this line to show a visual representation of the 
        # collisions occuring
        #base.cTrav.showCollisions(render)
        
        # Create some lighting
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor(Vec4(.3, .3, .3, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(Vec3(-5, -5, -5))
        directionalLight.setColor(Vec4(1, 1, 1, 1))
        directionalLight.setSpecularColor(Vec4(1, 1, 1, 1))
        render.setLight(render.attachNewNode(ambientLight))
        render.setLight(render.attachNewNode(directionalLight))
        
        taskMgr.add(self.move,"moveTask")

  

    
    # reinitialize all necessary parts of the game
    def restart(self):

        lives = lives - 1

        if lives == 0:
            sys.exit()

        self.numObjects = 10
        printNumObj(self.score)
        self.ralph.setPos(self.ralphStartPos)
        self.health = 100
        self.stamina = 100
        self.time = 0
        base.camera.setPos(0, 0, 0)
        base.camera.reparentTo(self.ralph)
        base.camera.setPos(0, 40, 2)
        base.camera.lookAt(self.ralph)
        self.placeCoins()
        self.placeCollectibles()
        taskMgr.add(self.move,"moveTask")
   
    
    # Display ralph's health
   
    # Display ralph's stamina
    def displayStamina(self):
        sprintBar['scale'] = (self.stamina*0.01*BAR_WIDTH,0.2,0.2)
    
    # Allow ralph to collect the health items
    def collectCoins(self, entry):
        # refill ralph's health
        print self.score
        printNumObj(self.score)
        self.score = self.numObjects + self.score * 10
        # reposition the collectible
        self.placeItem(entry.getIntoNodePath().getParent())
    
    def collectCollectibles(self, entry):
        # remove the collectible
        entry.getIntoNodePath().getParent().removeNode()
        # update the number of objects
        self.numObjects -= 1
        printNumObj(self.score)
        self.score = self.score + 500
        
    # Places an item randomly on the map    
    def placeItem(self, item):
        # Add ground collision detector to the health item
        self.collectGroundRay = CollisionRay()
        self.collectGroundRay.setOrigin(0,0,300)
        self.collectGroundRay.setDirection(0,0,-1)
        self.collectGroundCol = CollisionNode('colRay')
        self.collectGroundCol.addSolid(self.collectGroundRay)
        self.collectGroundCol.setFromCollideMask(BitMask32.bit(0))
        self.collectGroundCol.setIntoCollideMask(BitMask32.allOff())
        self.collectGroundColNp = item.attachNewNode(self.collectGroundCol)
        self.collectGroundHandler = CollisionHandlerQueue()
        base.cTrav.addCollider(self.collectGroundColNp, self.collectGroundHandler)
        
        placed = False;
        while placed == False:
            # re-randomize position
            item.setPos(-random.randint(0,140),-random.randint(0,40),0)
            
            base.cTrav.traverse(render)
            
            # Get Z position from terrain collision
            entries = []
            for j in range(self.collectGroundHandler.getNumEntries()):
                entry = self.collectGroundHandler.getEntry(j)
                entries.append(entry)
            entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(),
                                         x.getSurfacePoint(render).getZ()))
        
            if (len(entries)>0) and (entries[0].getIntoNode().getName() == "terrain"):
                item.setZ(entries[0].getSurfacePoint(render).getZ()+1)
                placed = True
                
        # remove placement collider
        self.collectGroundColNp.removeNode()
    
    def placeCoins(self):
        self.placeholder = render.attachNewNode("HealthItem-Placeholder")
        self.placeholder.setPos(0,0,0)
        
        # Add the health items to the placeholder node
        for i in range(5):
            # Load in the health item model
            self.healthy = loader.loadModel("models/sphere")
            self.healthy.setPos(0,0,0)
            self.healthy.reparentTo(self.placeholder)
            
            self.placeItem(self.healthy)
            
            # Add spherical collision detection
            healthSphere = CollisionSphere(0,0,0,1)
            sphereNode = CollisionNode('healthSphere')
            sphereNode.addSolid(healthSphere)
            sphereNode.setFromCollideMask(BitMask32.allOff())
            sphereNode.setIntoCollideMask(BitMask32.bit(0))
            sphereNp = self.healthy.attachNewNode(sphereNode)
            sphereColHandler = CollisionHandlerQueue()
            base.cTrav.addCollider(sphereNp, sphereColHandler)
            
    def placeCollectibles(self):
        self.placeCol = render.attachNewNode("Collectible-Placeholder")
        self.placeCol.setPos(0,0,0)
        
        # Add the health items to the placeCol node
        for i in range(self.rare):
            # Load in the health item model
            self.collect = loader.loadModel("models/jack")
            self.collect.setPos(0,0,0)
            self.collect.reparentTo(self.placeCol)
            
            self.placeItem(self.collect)
            
            # Add spherical collision detection
            colSphere = CollisionSphere(0,0,0,1)
            sphereNode = CollisionNode('colSphere')
            sphereNode.addSolid(colSphere)
            sphereNode.setFromCollideMask(BitMask32.allOff())
            sphereNode.setIntoCollideMask(BitMask32.bit(0))
            sphereNp = self.collect.attachNewNode(sphereNode)
            sphereColHandler = CollisionHandlerQueue()
            base.cTrav.addCollider(sphereNp, sphereColHandler)
        
    #Records the state of the arrow keys
    def setKey(self, key, value):
        self.keyMap[key] = value
    
    # Makes ralph's health decrease over time

    
    # Make ralph's stamina regenerate
    def staminaReg(self, task):
        if (self.stamina >= 100):
            self.stamina = 100
            return task.done
        else:
            self.stamina += 1
            task.setDelay(1)
            return task.again
        
    # Make ralph run
    def runRalph(self, arg):
        self.isRunning = arg
    
    # Accepts arrow keys to move either the player or the menu cursor,
    # Also deals with grid checking and collision detection
    def move(self, task):
        if self.numObjects != 0:
            # print the time
            self.time += globalClock.getDt()
            timeText['text'] = str(self.time)
        else:
            self.die()
        
        # save ralph's initial position so that we can restore it,
        # in case he falls off the map or runs into something.
        startpos = self.ralph.getPos()
        
        # calculate ralph's speed
        if (self.isRunning and self.stamina > 0):
            taskMgr.remove("staminaTask")
            ralphSpeed = 45
            self.stamina -= 0.5
        else:
            taskMgr.doMethodLater(5, self.staminaReg, "staminaTask")
            ralphSpeed = 25

        # If a move-key is pressed, move ralph in the specified direction.
        # and rotate the camera to remain behind ralph
        if (self.keyMap["left"]!=0):
            self.ralph.setH(self.ralph.getH() + 100 * globalClock.getDt())
        if (self.keyMap["right"]!=0):
            self.ralph.setH(self.ralph.getH() - 100 * globalClock.getDt())
        if (self.keyMap["forward"]!=0):
            self.ralph.setY(self.ralph, -ralphSpeed * globalClock.getDt())
        if (self.keyMap["backward"]!=0):
            self.ralph.setY(self.ralph, ralphSpeed *globalClock.getDt())

        # If ralph is moving, loop the run animation.
        # If he is standing still, stop the animation.
        if ((self.keyMap["forward"]!=0) or (self.keyMap["left"]!=0) 
            or (self.keyMap["right"]!=0) or (self.keyMap["backward"]!=0)):
            if self.isMoving is False:
                self.ralph.loop("run")
                self.isMoving = True
        else:
            if self.isMoving:
                self.ralph.stop()
                self.ralph.pose("walk",5)
                self.isMoving = False

        # so the following line is unnecessary
        base.cTrav.traverse(render)

        # Adjust ralph's Z coordinate.  If ralph's ray hit terrain,
        # update his Z. If it hit anything else, or didn't hit anything, put
        # him back where he was last frame.
        entries = []
        for i in range(self.ralphGroundHandler.getNumEntries()):
            entry = self.ralphGroundHandler.getEntry(i)
            entries.append(entry)
        entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(),
                                     x.getSurfacePoint(render).getZ()))
        if (len(entries)>0) and (entries[0].getIntoNode().getName() == "terrain"):
            self.ralph.setZ(entries[0].getSurfacePoint(render).getZ())
            #base.camera.setZ(entries[0].getSurfacePoint(render).getZ()+5)
        elif (len(entries)>0) and (entries[0].getIntoNode().getName() == "healthSphere"):
            self.collectCoins(entries[0])
        elif (len(entries)>0) and (entries[0].getIntoNode().getName() == "colSphere"):
            self.collectCollectibles(entries[0])
        else:
            self.ralph.setPos(startpos)
        
        # Keep the camera above the terrain
        entries = []
        for i in range(self.camGroundHandler.getNumEntries()):
            entry = self.camGroundHandler.getEntry(i)
            entries.append(entry)
        entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(),
                                     x.getSurfacePoint(render).getZ()))
        if (len(entries)>0) and (entries[0].getIntoNode().getName() == "terrain"):
            modZ = entries[0].getSurfacePoint(render).getZ()
            base.camera.setZ(20.0+modZ+(modZ-self.ralph.getZ()))
        
        self.floater.setPos(self.ralph.getPos())
        self.floater.setZ(self.ralph.getZ()+2.0)
        base.camera.lookAt(self.floater)
        
        self.displayStamina()

        return task.cont
    
    # Restart or End?
    def die(self):
        # end all running tasks
        taskMgr.remove("moveTask")
        taskMgr.remove("healthTask")
        
        # open the file
        f = open('scores.txt', 'r')
        
        # current name, time, and collected items score
        n = f.readline()
        t = f.readline()
        c = f.readline()
        
        # close the file
        f.close()
        
        # number of collected collectibles
        colObj = 10 - self.numObjects
        
        # enter new high score
        if int(c) < colObj or (int(c) == colObj and float(t) > self.time):
            self.label = DirectLabel(text="New High Score! Enter Your Name:",
                                      scale=.05, pos=(0,0,0.2))
            self.entry = DirectEntry(text="", scale=.05, initialText="",
                                      numLines=1, focus=1, pos=(-0.25,0,0),
                                       command=self.submitScore)
        else:
            # display high score
            self.highscore = OkDialog(dialogName="highscoreDialog", 
                                      text="Current High Score:\n\nName: " + n + "Time: " + t + "Items Collected: " + c,
                                      command=self.showDialog)
    
    def showDialog(self, arg):
        # cleanup highscore dialog
        self.highscore.cleanup()
        # display restart or exit dialog
        self.dialog = YesNoDialog(dialogName="endDialog",
                                   text="Would you like to continue?", 
                                   command=self.endResult)
    
    def submitScore(self, name):
        f = open('scores.txt', 'w')
        
        # add new high score
        value = name + '\n' + str(self.time) + '\n' + str(10 - self.numObjects)
        f.write(value)
        
        f.close()
        
        self.entry.remove()
        self.label.remove()
        
        self.dialog = YesNoDialog(dialogName="endDialog",
                                   text="Would you like to play again?",
                                    command=self.endResult)
    
    # Handle the dialog result
    def endResult(self, arg):
        if (arg):
            # cleanup the dialog box
            self.dialog.cleanup()
            # restart the game
            self.restart()
        else:
            sys.exit()

w = World()
run()