#Mighty Mountain - A Python/Panda 3D Game to show Algebra in Computer Code and Games
#Written By: AgentSpyname(Alexander Parsan) and MCPlayer81(Freddy Baker)
#Concept By: Nushaab Syed
#Under the GPL
#Camera Code Based of: RoamingRalph
#Inspired By: RoamingRalphEnhanced

import sys #Imports the sys module so we can eaisly end the game
from easygui import msgbox,choicebox, buttonbox, textbox,enterbox  #For data entry throughout the program
import MySQLdb #To write scores to an online scoreboard

#Simple Startup Screen
x = buttonbox(msg='Welcome to Mighty Mountain! Please select an option to start!', title='MightyMountain', choices=("Start Game", "View Scoreboard", "Quit"), image="Images/Start.png")
if x == "Start Game":
     name = enterbox("Please enter your name!")
     msgbox("Click OK To start the game!")
              
if x == "View Scoreboard":
    msgbox("Loading Scoreboard")

if x == "Quit":
    sys.exit()

#Panda3D Modules
import direct.directbase.DirectStart #Starts Panda3d
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
import time
import random, os, math


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
                          pos=(0.7, 0, 0.95), scale=(BAR_WIDTH,0.5,0.5))
sprintBar.setTransparency(TransparencyAttrib.MAlpha)

def printNumObj(n):
    numObjText['text'] = (str)(n)


class World(DirectObject):



    def __init__(self):
        #Let's start the Music
        mySound = base.loader.loadSfx("music/music.mp3")
        mySound.setLoopCount(0) #And Keep it On Loop
        mySound.play()
       

        base.setFrameRateMeter(True) #Shows the FrameRate in The Top Corner

        self.walking = Vec3()
        self.isMoving = False
        self.dest = None
        base.win.setClearColor(Vec4(0,0,0,1))


        self.keyMap = {"left":0, "right":0, "forward":0, "backward":0}
        base.win.setClearColor(Vec4(0,0,0,1))

        #Here is the number of collectibles in the game
        
        self.rare = 1; 
        self.vasenum = 10;
        self.coinnum = 30;
        self.silvernum = 5;
        self.chestnum = 2;

        #Here is the Obstacles in the game
        self.rocknum = 500;

        #Here is the Score
        self.score = 0;

        #Here is the total Number of Objects to collect
        self.numObjects = self.rare + self.vasenum + self.coinnum + self.silvernum + self.chestnum
   
        # print the number of objects
        printNumObj(self.score)

        # Post the instructions
        self.title = addTitle("Mighty Mountain")
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
        print self.ralphStartPos
        self.ralph = Actor("models/ralph",
                                 {"run":"models/ralph-run",
                                  "walk":"models/ralph-walk"})
        self.ralph.reparentTo(render)
        self.ralph.setScale(.2)
        self.ralph.setPos(self.ralphStartPos)


        # ralph's stamina
        self.stamina = 200
        # Create a floater object.  We use the "floater" as a temporary
        # variable in a variety of calculations.
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)

        # Accept the control keys for movement and rotation
        self.accept("escape", self.endgame)
        
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

        
        # Place the collectibles
        self.placeCollectibles() #Platinum 
        self.placeVases()
        self.placeCoins()
        self.placeSilver()
        self.placeGold()
        self.placeChests()

        #Place the obstacles
        self.placeRocks() #Cactus 
       
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


    #Reinitialize all necessary parts of the game
    def restart(self):

        #self.numObjects = 10
        self.score = 0
        printNumObj(self.score)
        self.ralph.setPos(self.ralphStartPos)
        self.stamina = 200
        self.time = 0
        base.camera.setPos(0, 0, 0)
        base.camera.reparentTo(self.ralph)
        base.camera.setPos(0, 40, 2)
        base.camera.lookAt(self.ralph)
        
        # Place the collectibles
        self.placeCollectibles() #Platinum 
        self.placeVases()
        self.placeCoins()
        self.placeSilver()
        self.placeGold()
        self.placeChests()

        #Place the obstacles
        self.placeRocks()

        #Total number of obstacles
        self.numObjects = self.rare + self.vasenum + self.coinnum + self.silvernum + self.chestnum

        taskMgr.add(self.move,"moveTask")
   
    
   
    # Display ralph's stamina
    def displayStamina(self):
        sprintBar['scale'] = (self.stamina*0.01*BAR_WIDTH,0.2,0.2)
    
#Collects the item and modifies score

    def collectCollectibles(self, entry): #Platinum 
        #Remove the collectible
        entry.getIntoNodePath().getParent().removeNode()
        # Update the number of objects
        self.score = self.score * self.numObjects + 500
        self.numObjects = self.numObjects - 1
        printNumObj(self.score)
        

    def collectVase(self, entry):
        # Remove the collectible
        entry.getIntoNodePath().getParent().removeNode()
        # Update the number of objects
        self.score = self.score + 10
        self.numObjects = self.numObjects - 1
        printNumObj(self.score)
    
    def collectCoins(self, entry):
        # Remove the collectible
        entry.getIntoNodePath().getParent().removeNode()
        # Update the number of objects
        self.score = self.score + 1
        printNumObj(self.score)
        self.numObjects = self.numObjects - 1


    def collectSilver(self, entry):
        # Remove the collectible
        entry.getIntoNodePath().getParent().removeNode()
        # Update the number of objects
        self.score = self.score + 20
        printNumObj(self.score)
        self.numObjects = self.numObjects - 1


    def collectGold(self, entry):
        # Remove the collectible
        entry.getIntoNodePath().getParent().removeNode()
        # Update the number of objects
        self.score = self.score + 30
        printNumObj(self.score)
        self.numObjects = self.numObjects - 1

    def collectChest(self, entry):
        # Remove the collectible
        entry.getIntoNodePath().getParent().removeNode()
        # Update the number of objects
        self.score = self.score + 100
        printNumObj(self.score)
        self.numObjects = self.numObjects - 1

#Unique function which handles collisions with a deduction obstacles.
    def deductRocks(self, entry):
        # Remove the collectible
        entry.getIntoNodePath().getParent().removeNode()
        # Update the number of objects
        if self.score > 500:
            randomnum = random.randint(1,2)
            if randomnum == 1:
             self.score = self.score - 100 #Removes Score
            if randomnum == 2:
             self.score = self.score + 100 #Removes Score

        if self.score < 500:
            self.score = self.score - 100

        randomnum = random.randint(1,2)

        if randomnum == 1:
            result =buttonbox(msg='A kind wizard wishes to help you on your quest? Trust him?', title='Alert!', choices=("Yes", "No"))

            if result == "Yes":
                othernum = random.randint(1,100)
                othernum = othernum * self.score + self.numObjects #Y = MX + B

                if othernum > 1000:
                    msgbox("Good choice! Add 1,000 Points to your Score!")
                    self.score = self.score + 1000
                if othernum < 1000:
                    msgbox("The wizard tricked you!He stole 100 Points!")
                    self.score = self.score - 100

        printNumObj(self.score)
      
      
        
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
    
   
#Places all obstacles on map.          
    def placeCollectibles(self):
        self.placeCol = render.attachNewNode("Collectible-Placeholder")
        self.placeCol.setPos(0,0,0)
        
        # Add the health items to the placeCol node
        for i in range(self.rare):
            # Load in the health item model
            self.collect = loader.loadModel("models/moneyBag")
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

    def placeVases(self):
        self.placeV = render.attachNewNode("Collectible-Placeholder")
        self.placeV.setPos(0,0,0)
        
        # Add the health items to the placeCol node
        for i in range(self.vasenum):
            # Load in the health item model
            self.collect = loader.loadModel("models/jar.egg")
            self.collect.setPos(0,0,0)
            self.collect.reparentTo(self.placeV)
            
            self.placeItem(self.collect)
            
            # Add spherical collision detection
            vaseSphere = CollisionSphere(0,0,0,1)
            sphereNode = CollisionNode('vaseSphere')
            sphereNode.addSolid(vaseSphere)
            sphereNode.setFromCollideMask(BitMask32.allOff())
            sphereNode.setIntoCollideMask(BitMask32.bit(0))
            sphereNp = self.collect.attachNewNode(sphereNode)
            sphereColHandler = CollisionHandlerQueue()
            base.cTrav.addCollider(sphereNp, sphereColHandler)

    def placeCoins(self):
        self.placeC = render.attachNewNode("Collectible-Placeholder")
        self.placeC.setPos(0,0,0)
        
        # Add the health items to the placeCol node
        for i in range(self.coinnum):
            # Load in the health item model
            self.collect = loader.loadModel("models/Cookie.egg")
            self.collect.setPos(0,0,0)
            self.collect.reparentTo(self.placeC)
            
            self.placeItem(self.collect)
            
            # Add spherical collision detection
            coinSphere = CollisionSphere(0,0,0,1)
            sphereNode = CollisionNode('coinSphere')
            sphereNode.addSolid(coinSphere)
            sphereNode.setFromCollideMask(BitMask32.allOff())
            sphereNode.setIntoCollideMask(BitMask32.bit(0))
            sphereNp = self.collect.attachNewNode(sphereNode)
            sphereColHandler = CollisionHandlerQueue()
            base.cTrav.addCollider(sphereNp, sphereColHandler)

    def placeSilver(self):
        self.placeS = render.attachNewNode("Collectible-Placeholder")
        self.placeS.setPos(0,0,0)
        
        # Add the health items to the placeCol node
        for i in range(self.silvernum):
            # Load in the health item model
            self.collect = loader.loadModel("models/Anvil.egg")
            self.collect.setPos(0,0,0)
            self.collect.reparentTo(self.placeS)
            
            self.placeItem(self.collect)
            
            # Add spherical collision detection
            silverSphere = CollisionSphere(0,0,0,1)
            sphereNode = CollisionNode('silverSphere')
            sphereNode.addSolid(silverSphere)
            sphereNode.setFromCollideMask(BitMask32.allOff())
            sphereNode.setIntoCollideMask(BitMask32.bit(0))
            sphereNp = self.collect.attachNewNode(sphereNode)
            sphereColHandler = CollisionHandlerQueue()
            base.cTrav.addCollider(sphereNp, sphereColHandler)

    def placeGold(self):
        self.placeG = render.attachNewNode("Collectible-Placeholder")
        self.placeG.setPos(0,0,0)
        
        # Add the health items to the placeCol node
        for i in range(self.silvernum):
            # Load in the health item model
            self.collect = loader.loadModel("models/key.egg")
            self.collect.setPos(0,0,0)
            self.collect.reparentTo(self.placeS)
            
            self.placeItem(self.collect)
            
            # Add spherical collision detection
            goldSphere = CollisionSphere(0,0,0,1)
            sphereNode = CollisionNode('goldSphere')
            sphereNode.addSolid(goldSphere)
            sphereNode.setFromCollideMask(BitMask32.allOff())
            sphereNode.setIntoCollideMask(BitMask32.bit(0))
            sphereNp = self.collect.attachNewNode(sphereNode)
            sphereColHandler = CollisionHandlerQueue()
            base.cTrav.addCollider(sphereNp, sphereColHandler)
    def placeChests(self):
        self.placeCh = render.attachNewNode("Collectible-Placeholder")
        self.placeCh.setPos(0,0,0)
        
        # Add the health items to the placeCol node
        for i in range(self.chestnum):
            # Load in the health item model
            self.collect = loader.loadModel("models/Keg.a2c.cr.egg")
            self.collect.setPos(0,0,0)
            self.collect.reparentTo(self.placeCh)
            
            self.placeItem(self.collect)
            
            # Add spherical collision detection
            chestSphere = CollisionSphere(0,0,0,1)
            sphereNode = CollisionNode('chestSphere')
            sphereNode.addSolid(chestSphere)
            sphereNode.setFromCollideMask(BitMask32.allOff())
            sphereNode.setIntoCollideMask(BitMask32.bit(0))
            sphereNp = self.collect.attachNewNode(sphereNode)
            sphereColHandler = CollisionHandlerQueue()
            base.cTrav.addCollider(sphereNp, sphereColHandler)

    def placeRocks(self):
        self.placeR = render.attachNewNode("Collectible-Placeholder")
        self.placeR.setPos(0,0,0)
        
        # Add the health items to the placeCol node
        for i in range(self.rocknum):
            # Load in the health item model
            self.collect = loader.loadModel("models/smallcactus.egg")
            self.collect.setScale(0.2)
            self.collect.setPos(0,0,0)
            self.collect.reparentTo(self.placeR)
            
            self.placeItem(self.collect)
            
            # Add spherical collision detection
            rockSphere = CollisionSphere(0,0,0,1)
            sphereNode = CollisionNode('rockSphere')
            sphereNode.addSolid(rockSphere)
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
        if (self.stamina >= 200):
            self.stamina = 200
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
        if self.score < 0:
            self.die()

        if self.numObjects == 0:
            self.endgame()

        randomnum1 = random.randint(1,1000)
        randomnum2 = randomnum1 * self.numObjects + self.score

        if randomnum1 == 1000:
            result =buttonbox(msg='An odd villager wishes to help you on your quest? Trust him?', title='Alert!', choices=("Yes", "No"))
            if result == "Yes":
                if randomnum2 > 20000:
                    msgbox("The villager grants you 4,000 Points!")
                if randomnum2 < 20000:
                    msgbox("The villager betrays you! He steal 200 points!")

        
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

        #Adds all the items to the map and handles if they get hit.
        elif (len(entries)>0) and (entries[0].getIntoNode().getName() == "colSphere"):
            self.collectCollectibles(entries[0])
        elif (len(entries)>0) and (entries[0].getIntoNode().getName() == "vaseSphere"):
            self.collectVase(entries[0])
        elif (len(entries)>0) and (entries[0].getIntoNode().getName() == "coinSphere"):
            self.collectCoins(entries[0])
        elif (len(entries)>0) and (entries[0].getIntoNode().getName() == "silverSphere"):
            self.collectSilver(entries[0])
        elif (len(entries)>0) and (entries[0].getIntoNode().getName() == "goldSphere"):
            self.collectGold(entries[0])
        elif (len(entries)>0) and (entries[0].getIntoNode().getName() == "chestSphere"):
            self.collectChest(entries[0])
        elif (len(entries)>0) and (entries[0].getIntoNode().getName() == "rockSphere"):
            self.deductRocks(entries[0])

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
    #If the user collects all items and/or ends the game through Escape.
    def endgame(self):
         # end all running tasks
        taskMgr.remove("moveTask")
        taskMgr.remove("healthTask")

        # Open database connection and inserts data.
        conn = MySQLdb.connect("sql5.freemysqlhosting.net","sql5106009","DFxbmhVkvG","sql5106009")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO scores (score, username) VALUES (%s, %s)", (self.score, name))
        conn.commit()
        time.sleep(5) #Error without this...

        #Some text
        self.label = DirectLabel(text="End Game!",
                                      scale=.05, pos=(0,0,0.2))

        self.entry = DirectEntry(text="", scale=.05, initialText="",
                                    numLines=1, focus=1, pos=(-0.25,0,0))

        
   
        #Display high score

        self.highscore = OkDialog(dialogName="highscoreDialog", 
                                  text="Your High Score:\n\nName: " + name + "Score: " + str(self.score),
                                  command=sys.exit())

    # Restart or End?
    def die(self):
        # end all running tasks
        taskMgr.remove("moveTask")
        taskMgr.remove("healthTask")

        # Open database connection
        conn = MySQLdb.connect("sql5.freemysqlhosting.net","sql5106009","DFxbmhVkvG","sql5106009")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO scores (score, username) VALUES (%s, %s)", (self.score, name))
        conn.commit()
        time.sleep(5)

        self.label = DirectLabel(text="Game over!",
                                      scale=.05, pos=(0,0,0.2))

        self.entry = DirectEntry(text="", scale=.05, initialText="",
                                    numLines=1, focus=1, pos=(-0.25,0,0))

        
   
        #Display high score

        self.highscore = OkDialog(dialogName="highscoreDialog", 
                                  text="Your High Score:\n\nName: " + name + " " + "Score: " + str(self.score),
                                  command=self.showDialog)


    def showDialog(self, arg):
        # cleanup highscore dialog
        self.highscore.cleanup()
        # display restart or exit dialog
        self.dialog = YesNoDialog(dialogName="endDialog",
                                   text="Would you like to continue?", 
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
