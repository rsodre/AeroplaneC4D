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

def RotMatrix(m):
	return c4d.Matrix( c4d.Vector(), m.v1, m.v2, m.v3 )

class Aeroplane(plugins.TagData):
	"""Aeroplane"""
	
	cam_ = None
	plane_ = None

	def save_camera(self, tag):
		#print "Aeroplane ON"
		data = tag.GetDataInstance()
		if self.cam_:
			data.SetVector( c4d.AEROPLANE_CAM_ROT, self.cam_.GetAbsRot() )
			data.SetFloat( c4d.AEROPLANE_CAM_FOV, self.cam_[c4d.CAMERAOBJECT_FOV_VERTICAL] )
			data.SetFloat( c4d.AEROPLANE_CAM_OFFX, self.cam_[c4d.CAMERAOBJECT_FILM_OFFSET_X] )
			data.SetFloat( c4d.AEROPLANE_CAM_OFFY, self.cam_[c4d.CAMERAOBJECT_FILM_OFFSET_Y] )
		if self.plane_:
			data.SetBool( c4d.AEROPLANE_PLANE_XRAY, self.plane_[c4d.ID_BASEOBJECT_XRAY] )

	def restore_camera(self, tag):
		#print "Aeroplane OFF"
		data = tag.GetDataInstance()
		if self.cam_:
			ctag = self.cam_.GetTag(1019364) # Constraint tag
			if ctag:
				ctag[c4d.ID_CA_CONSTRAINT_TAG_PSR] = False
				ctag.Remove()
			self.cam_.SetAbsRot( data.GetVector( c4d.AEROPLANE_CAM_ROT ) )
			self.cam_[c4d.CAMERAOBJECT_FOV_VERTICAL] = data.GetFloat( c4d.AEROPLANE_CAM_FOV )
			self.cam_[c4d.CAMERAOBJECT_FILM_OFFSET_X] = data.GetFloat( c4d.AEROPLANE_CAM_OFFX )
			self.cam_[c4d.CAMERAOBJECT_FILM_OFFSET_Y] = data.GetFloat( c4d.AEROPLANE_CAM_OFFY )
		if self.plane_:
			self.plane_[c4d.ID_BASEOBJECT_XRAY] = data.GetBool( c4d.AEROPLANE_PLANE_XRAY )

	def Init(self, node):
		data = node.GetDataInstance()
		data.SetBool( c4d.AEROPLANE_ENABLED, True )
		data.SetVector( c4d.AEROPLANE_CAM_ROT, c4d.Vector() )
		data.SetFloat( c4d.AEROPLANE_CAM_FOV, 0.0 )
		data.SetFloat( c4d.AEROPLANE_CAM_OFFX, 0.0 )
		data.SetFloat( c4d.AEROPLANE_CAM_OFFY, 0.0 )
		data.SetFloat( c4d.ID_BASEOBJECT_XRAY, False )

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
		self.plane_ = data.GetLink(c4d.AEROPLANE_LINK)

		# Check if is enabled
		isEnabled = False
		if op.IsInstanceOf( c4d.Ocamera ):
			self.cam_ = op
			if self.plane_ is not None and data.GetBool( c4d.AEROPLANE_ENABLED ):
				isEnabled = True

		wasEnabled = data.GetBool( c4d.AEROPLANE_SAVED )
		
		# Disabled
		if not isEnabled:
			if wasEnabled:
				self.restore_camera(tag)
				data.SetBool( c4d.AEROPLANE_SAVED, False )
			return c4d.EXECUTIONRESULT_OK
		
		# Enabled
		if not wasEnabled:
			self.save_camera(tag)
			data.SetBool( c4d.AEROPLANE_SAVED, True )

		# Create constraint tag
		ctag = self.cam_.GetTag(1019364) # Constraint tag
		if ctag is None: ctag = self.cam_.MakeTag(1019364, tag)
		if ctag is None: return c4d.EXECUTIONRESULT_OK
		
		camVec = c4d.Vector( 0, c4d.utils.DegToRad( -90 ), 0 ).GetNormalized()
		planeVec = self.plane_.GetAbsRot().GetNormalized()
		angle = -math.acos( planeVec * camVec )
		angle = c4d.utils.DegToRad(-90)

		ctag.SetName('Aeroplane')
		ctag[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
		ctag[c4d.ID_CA_CONSTRAINT_TAG_PSR_R_OFFSET] = c4d.Vector( 0, c4d.utils.DegToRad( -90 ), 0 )
		#ctag[c4d.ID_CA_CONSTRAINT_TAG_PSR_R_OFFSET] = c4d.Vector( 0, angle, 0 )
		ctag[10005] = False			# P
		ctag[10006] = False			# S
		ctag[10007] = True			# R
		ctag[10001] = self.plane_	# Target

		rd = doc.GetActiveRenderData()
		renderWidth = float( rd[c4d.RDATA_XRES] )
		renderHeight = float( rd[c4d.RDATA_YRES] )
		renderAspect = ( renderWidth / renderHeight )

		planeWidth = self.plane_[c4d.PRIM_PLANE_WIDTH]
		planeHeight = self.plane_[c4d.PRIM_PLANE_HEIGHT]
		planeAspect = ( planeWidth / planeHeight )
		
		# Fit plane to render area
		if planeAspect < renderAspect:
			planeWidth = planeHeight * renderAspect
		elif planeAspect > renderAspect:
			planeHeight = planeWidth / renderAspect

		camMat = self.cam_.GetMg()
		planeMat = self.plane_.GetMg()
		
		# plane must always be facing the camera
		planeRotMat = RotMatrix( planeMat )
		planeVec = c4d.Vector(0,1,0) * planeRotMat
		camVec = (camMat.off - planeMat.off).GetNormalized()
		dot = c4d.Vector.Dot( camVec, planeVec )
		if dot < 0:
			planeMat *= c4d.utils.MatrixScale( c4d.Vector(1,-1,-1) )
			self.plane_.SetMg( planeMat )
			planeRotMat = RotMatrix( planeMat )

		# Rotate delta vector to face down
		delta = camMat.off - planeMat.off
		delta *= ~planeRotMat
		#delta += planeMat.off

		distance = abs( delta.y )
		fov = math.atan2( planeHeight/2, distance )
		offx = -(delta.x / planeWidth)
		offy = (delta.z / planeHeight)
		#print "delta %s dist %.1f off %.2f %.2f fov %.1f" % (str(delta),distance,offx,offy,c4d.utils.RadToDeg(fov))
		
		self.cam_[c4d.CAMERAOBJECT_FOV_VERTICAL] = fov * 2
		self.cam_[c4d.CAMERAOBJECT_FILM_OFFSET_X] = offx
		self.cam_[c4d.CAMERAOBJECT_FILM_OFFSET_Y] = offy
		self.plane_[c4d.ID_BASEOBJECT_XRAY] = True

		self.cam_.Message(c4d.MSG_UPDATE)
		self.plane_.Message(c4d.MSG_UPDATE)
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
