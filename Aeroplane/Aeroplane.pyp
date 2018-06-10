#
# AeroplaneC4D
# Asymmetric Camera for Cinema 4D
# Created by Roger Sodré, Jun 2018 @ Cochabamba, Bolivia
# https://github.com/rsodre/AeroplaneC4D
#

import os
import math
import c4d
from c4d import bitmaps, plugins, utils

# This ID is exclusive for this plugin, using the same will cause conflicts
# Get your own ID at Plugin Cafe, or use 1000001-1000010 for development
# http://www.plugincafe.com/forum/developer.asp
PLUGIN_ID = 1041240

wasEnabled_ = False
cam_ = None

class Aeroplane(plugins.TagData):
	"""Aeroplane"""
	
	def save_camera(self, tag):
		print "Aeroplane ON"
		global cam_
		if cam_:
			data = tag.GetDataInstance()
			data.SetVector( c4d.AEROPLANE_CAM_ROT, cam_.GetAbsRot() )
			data.SetFloat( c4d.AEROPLANE_CAM_FOV, cam_[c4d.CAMERAOBJECT_FOV_VERTICAL] )
			data.SetFloat( c4d.AEROPLANE_CAM_OFFX, cam_[c4d.CAMERAOBJECT_FILM_OFFSET_X] )
			data.SetFloat( c4d.AEROPLANE_CAM_OFFY, cam_[c4d.CAMERAOBJECT_FILM_OFFSET_Y] )

	def restore_camera(self, tag):
		print "Aeroplane OFF"
		global cam_
		if cam_:
			ctag = cam_.GetTag(1019364) # Constraint tag
			if ctag:
				ctag[c4d.ID_CA_CONSTRAINT_TAG_PSR] = False
				ctag.Remove()
			data = tag.GetDataInstance()
			cam_.SetAbsRot( data.GetVector( c4d.AEROPLANE_CAM_ROT ) )
			cam_[c4d.CAMERAOBJECT_FOV_VERTICAL] = data.GetFloat( c4d.AEROPLANE_CAM_FOV )
			cam_[c4d.CAMERAOBJECT_FILM_OFFSET_X] = data.GetFloat( c4d.AEROPLANE_CAM_OFFX )
			cam_[c4d.CAMERAOBJECT_FILM_OFFSET_Y] = data.GetFloat( c4d.AEROPLANE_CAM_OFFY )
	
	def Init(self, node):
		data = node.GetDataInstance()
		data.SetBool( c4d.AEROPLANE_ENABLED, True )
		data.SetBool( c4d.AEROPLANE_FLIP, False )
		data.SetVector( c4d.AEROPLANE_CAM_ROT, c4d.Vector() )
		data.SetFloat( c4d.AEROPLANE_CAM_FOV, 0.0 )
		data.SetFloat( c4d.AEROPLANE_CAM_OFFX, 0.0 )
		data.SetFloat( c4d.AEROPLANE_CAM_OFFY, 0.0 )

		pd = node[c4d.EXPRESSION_PRIORITY]
		if pd is not None:
			pd.SetPriorityValue(c4d.PRIORITYVALUE_CAMERADEPENDENT, True)
			node[c4d.EXPRESSION_PRIORITY] = pd
		
		return True
	
	def Execute(self, tag, doc, op, bt, priority, flags):
		bd = doc.GetRenderBaseDraw()
		if bd is None: return c4d.EXECUTIONRESULT_OK
		data = tag.GetDataInstance()
		if data is None: return c4d.EXECUTIONRESULT_OK
		plane = data.GetLink(c4d.AEROPLANE_LINK)

		global wasEnabled_
		global cam_

		# Check if is enabled
		isEnabled = False
		if op.IsInstanceOf( c4d.Ocamera ):
			cam_ = op
			if plane is not None and data.GetBool( c4d.AEROPLANE_ENABLED ):
				isEnabled = True

		# Disabled
		if not isEnabled:
			if wasEnabled_:
				self.restore_camera(tag)
				wasEnabled_ = False
			return c4d.EXECUTIONRESULT_OK
		
		# Enabled
		if not wasEnabled_:
			self.save_camera(tag)
			wasEnabled_ = True

		# Create constraint tag
		ctag = cam_.GetTag(1019364) # Constraint tag
		if ctag is None: ctag = cam_.MakeTag(1019364, tag)
		if ctag is None: return c4d.EXECUTIONRESULT_OK

		ctag.SetName('Aeroplane')
		ctag[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
		ctag[c4d.ID_CA_CONSTRAINT_TAG_PSR_R_OFFSET] = c4d.Vector( 0, c4d.utils.DegToRad( -90 ), 0 )
		ctag[10005] = False		# P
		ctag[10006] = False		# S
		ctag[10007] = True		# R
		ctag[10001] = plane		# Target
		
		rd = doc.GetActiveRenderData()
		renderWidth = float( rd[c4d.RDATA_XRES] )
		renderHeight = float( rd[c4d.RDATA_YRES] )
		aspect = renderWidth / renderHeight

		#width = plane[c4d.PRIM_PLANE_WIDTH]
		height = plane[c4d.PRIM_PLANE_HEIGHT]
		width = height * aspect

		camPos = cam_.GetMg().off
		planePos = plane.GetMg().off
		delta = camPos - planePos
		distance = abs( delta.y )
		fov = math.atan2( height/2, distance )
		#print "height %s dist %s fov %s" % (str(height),str(distance),str(c4d.utils.RadToDeg(fov)))
		
		offx = (delta.x / width)
		offy = (delta.z / height)
		cam_[c4d.CAMERAOBJECT_FOV_VERTICAL] = fov * 2
		cam_[c4d.CAMERAOBJECT_FILM_OFFSET_X] = -offx
		cam_[c4d.CAMERAOBJECT_FILM_OFFSET_Y] = offy

		cam_.Message(c4d.MSG_UPDATE)
		c4d.EventAdd()

		return c4d.EXECUTIONRESULT_OK


if __name__ == "__main__":
	bmp = bitmaps.BaseBitmap()
	dir, file = os.path.split(__file__)
	fn = os.path.join(dir, "res", "TAeroplane.tif")
	bmp.InitWith(fn)
	plugins.RegisterTagPlugin(id=PLUGIN_ID,
							  str="Aeroplane",
							  info=c4d.TAG_EXPRESSION|c4d.TAG_VISIBLE,
							  g=Aeroplane,
							  description="TAeroplane",
							  icon=bmp)
