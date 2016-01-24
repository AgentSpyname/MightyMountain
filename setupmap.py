from panda3d.core import GeoMipTerrain

terrain = GeoMipTerrain("worldTerrain")
terrain.setHeightfield("heightmap.jpg")
terrain.setColorMap("colourmap.jpg")
# terrain.setBlockSize(512)
terrain.setBruteforce(True)

root = terrain.getRoot()
# root.reparentTo(render)
# root.setScale(0.5,0.5,0.5)
# root.setPos(0,0,0)
root.setSz(60) # max height

terrain.generate()
root.writeBamFile('mountain.bam')