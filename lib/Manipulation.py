#!/usr/bin/python

### import guacamole libraries ###
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed
import avango.daemon

### import framework libraries ###
from lib.Intersection import *

### import python libraries ###
# ...



class ManipulationManagerScript(avango.script.Script):

	## input fields
	sf_key_1 = avango.SFBool()
	sf_key_2 = avango.SFBool()
	sf_key_3 = avango.SFBool()
	sf_key_4 = avango.SFBool()


	## constructor
	def __init__(self):
		self.super(ManipulationManagerScript).__init__()

		### external references ###
		self.CLASS = None # is set later

		### resources ###
		self.keyboard_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
		self.keyboard_sensor.Station.value = "device-keyboard"

		self.sf_key_1.connect_from(self.keyboard_sensor.Button12) # key 1
		self.sf_key_2.connect_from(self.keyboard_sensor.Button13) # key 2
		self.sf_key_3.connect_from(self.keyboard_sensor.Button14) # key 3
		self.sf_key_4.connect_from(self.keyboard_sensor.Button15) # key 4

	
	def my_constructor(self, CLASS):
		self.CLASS = CLASS


	### callbacks ###
	@field_has_changed(sf_key_1)
	def sf_key_1_changed(self):
		if self.sf_key_1.value == True and self.CLASS is not None: # key is pressed
			self.CLASS.set_manipulation_technique(0) # switch to Virtual-Ray manipulation technique
			

	@field_has_changed(sf_key_2)
	def sf_key_2_changed(self):
		if self.sf_key_2.value == True and self.CLASS is not None: # key is pressed
			self.CLASS.set_manipulation_technique(1) # switch to Virtual-Hand manipulation technique


	@field_has_changed(sf_key_3)
	def sf_key_3_changed(self):
		if self.sf_key_3.value == True and self.CLASS is not None: # key is pressed
			self.CLASS.set_manipulation_technique(2) # switch to Go-Go manipulation technique


	@field_has_changed(sf_key_4)
	def sf_key_4_changed(self):
		if self.sf_key_4.value == True and self.CLASS is not None: # key is pressed
			self.CLASS.set_manipulation_technique(3) # switch to HOMER manipulation technique

		

class ManipulationManager:

	## constructor
	def __init__( self
				, SCENEGRAPH = None
				, PARENT_NODE = None
				, POINTER_TRACKING_STATION = ""
				, TRACKING_TRANSMITTER_OFFSET = avango.gua.make_identity_mat()
				, POINTER_DEVICE_STATION = ""
				, HEAD_NODE = None
				):


		### external references ###
		self.HEAD_NODE = HEAD_NODE
		

		### variables ###
		self.active_manipulation_technique = None


		### resources ###
	
		## init intersection
		self.intersection = Intersection(SCENEGRAPH = SCENEGRAPH)

		## init sensors
		self.pointer_tracking_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
		self.pointer_tracking_sensor.Station.value = POINTER_TRACKING_STATION
		self.pointer_tracking_sensor.TransmitterOffset.value = TRACKING_TRANSMITTER_OFFSET
			
		self.pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
		self.pointer_device_sensor.Station.value = POINTER_DEVICE_STATION


		## init manipulation techniques
		self.virtualRay = VirtualRay()
		self.virtualRay.my_constructor(MANIPULATION_MANAGER = self, PARENT_NODE = PARENT_NODE)

		self.virtualHand = VirtualHand()
		self.virtualHand.my_constructor(MANIPULATION_MANAGER = self, PARENT_NODE = PARENT_NODE)

		self.goGo = GoGo()
		self.goGo.my_constructor(MANIPULATION_MANAGER = self, PARENT_NODE = PARENT_NODE)

		self.homer = Homer()
		self.homer.my_constructor(MANIPULATION_MANAGER = self, PARENT_NODE = PARENT_NODE)

		
		## init script    
		self.script = ManipulationManagerScript()
		self.script.my_constructor(self)


		### set initial states ###
		self.set_manipulation_technique(0) # switch to virtual-ray manipulation technique


	### functions ###
	def set_manipulation_technique(self, INT):
		# evtl. disable prior technique
		if self.active_manipulation_technique is not None:
			self.active_manipulation_technique.enable(False)
	
		# enable new technique
		if INT == 0: # virtual-ray
			print("switch to virtual-ray technique")
			self.active_manipulation_technique = self.virtualRay

		elif INT == 1: # virtual-hand
			print("switch to virtual-hand technique")
			self.active_manipulation_technique = self.virtualHand

		elif INT == 2: # virtual-hand
			print("switch to go-go technique")
			self.active_manipulation_technique = self.goGo

		elif INT == 3: # HOMER
			print("switch to HOMER technique")
			self.active_manipulation_technique = self.homer
			
		self.active_manipulation_technique.enable(True)



class ManipulationTechnique(avango.script.Script):

	## input fields
	sf_drag_button = avango.SFBool()

	## constructor
	def __init__(self):
		self.super(ManipulationTechnique).__init__()
			   

	def my_constructor( self
					  , MANIPULATION_MANAGER = None
					  , PARENT_NODE = None
					  ):

		### external references ###
		self.MANIPULATION_MANAGER = MANIPULATION_MANAGER
		self.PARENT_NODE = PARENT_NODE

	
		### variables ###
		self.enable_flag = False
		
		self.first_pick_result = None

		self.dragged_node = None
		self.dragging_offset_mat = avango.gua.make_identity_mat()


		### resources ###

		## init nodes
		self.pointer_node = avango.gua.nodes.TransformNode(Name = "pointer_node")
		self.pointer_node.Transform.connect_from(MANIPULATION_MANAGER.pointer_tracking_sensor.Matrix)
		if PARENT_NODE is not None:
			PARENT_NODE.Children.value.append(self.pointer_node)
		
		self.tool_node = avango.gua.nodes.TransformNode(Name = "tool_node")
		self.tool_node.Tags.value = ["invisible"]
		self.pointer_node.Children.value.append(self.tool_node)


		## init field connections
		self.sf_drag_button.connect_from(MANIPULATION_MANAGER.pointer_device_sensor.Button0)


		## set global evaluation policy
		self.always_evaluate(True)



	### functions ###
	def enable(self, FLAG):
		self.enable_flag = FLAG
		
		if self.enable_flag == True:
			self.tool_node.Tags.value = [] # set tool visible
		else:
			self.stop_dragging() # evtl. stop active dragging process
			
			self.tool_node.Tags.value = ["invisible"] # set tool invisible



	### callbacks ###
	def evaluate(self):
		raise NotImplementedError("To be implemented by a subclass.")


	@field_has_changed(sf_drag_button)
	def sf_drag_button_changed(self):
		if self.enable_flag == True and self.sf_drag_button.value == True and self.first_pick_result is not None: # button pressed and intersection targetst found --> start dragging
			_node = self.first_pick_result.Object.value # get geometry node
			#print(_node, _node.Name.value)

			self.start_dragging(_node)

		elif self.sf_drag_button.value == False and self.dragged_node is not None: # button released and active dragging operation --> stop dragging
			self.stop_dragging()
			
		

	### functions ###
	def start_dragging(self, NODE):          
		#self.dragged_node = NODE
		self.dragged_node = NODE.Parent.value # take the group node of the geomtry node
		self.dragging_offset_mat = avango.gua.make_inverse_mat(self.tool_node.WorldTransform.value) * self.dragged_node.Transform.value # object transformation in pointer coordinate system

  
	def stop_dragging(self): 
		self.dragged_node = None
		self.dragging_offset_mat = avango.gua.make_identity_mat()


	def dragging(self):
		if self.dragged_node is not None: # object to drag
			self.dragged_node.Transform.value = self.tool_node.WorldTransform.value * self.dragging_offset_mat
			


class VirtualRay(ManipulationTechnique):

	## constructor
	def __init__(self):
		self.super(VirtualRay).__init__()


	def my_constructor( self
					  , MANIPULATION_MANAGER = None                      
					  , PARENT_NODE = None
					  ):

		ManipulationTechnique.my_constructor(self, MANIPULATION_MANAGER = MANIPULATION_MANAGER, PARENT_NODE = PARENT_NODE)


		### further parameters ###  
		self.ray_length = 2.0 # in meter
		self.ray_thickness = 0.005 # in meter

		self.intersection_point_size = 0.01 # in meter


		### further resources ###
		_loader = avango.gua.nodes.TriMeshLoader()

		self.ray_geometry = _loader.create_geometry_from_file("ray_geometry", "data/objects/cylinder.obj", avango.gua.LoaderFlags.DEFAULTS)
		self.ray_geometry.Transform.value = avango.gua.make_trans_mat(0.0,0.0,self.ray_length * -0.5) * \
											avango.gua.make_rot_mat(-90.0,1,0,0) * \
											avango.gua.make_scale_mat(self.ray_thickness, self.ray_length, self.ray_thickness)
		self.ray_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
		self.tool_node.Children.value.append(self.ray_geometry)

		self.intersection_geometry = _loader.create_geometry_from_file("intersection_geometry", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS)
		self.intersection_geometry.Tags.value = ["invisible"] # set geometry invisible
		self.intersection_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
		self.tool_node.Children.value.append(self.intersection_geometry)
		 

	### callbacks ###
	
	## implement base class function
	def evaluate(self):
	
		if self.enable_flag == True:    
			## calc intersection
			_mf_pick_result = self.MANIPULATION_MANAGER.intersection.calc_pick_result(PICK_MAT = self.tool_node.WorldTransform.value, PICK_LENGTH = self.ray_length)
			#print(len(_mf_pick_result.value))

			if len(_mf_pick_result.value) > 0: # intersection found
				self.first_pick_result = _mf_pick_result.value[0] # get first pick result
			
			else: # no intersection found
				self.first_pick_result = None
  
 
			if self.first_pick_result is not None:
				_point = self.first_pick_result.WorldPosition.value
				_distance = (self.tool_node.WorldTransform.value.get_translate() - _point).length()
				
				## update ray length visualization
				self.ray_geometry.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, _distance * -0.5) * \
													avango.gua.make_rot_mat(-90.0, 1, 0, 0) * \
													avango.gua.make_scale_mat(self.ray_thickness, _distance, self.ray_thickness)
  

				## update intersection point visualization
				self.intersection_geometry.Transform.value = avango.gua.make_trans_mat(0.0,0.0,-_distance) * \
															 avango.gua.make_scale_mat(self.intersection_point_size)
																  
				self.intersection_geometry.Tags.value = [] # set visible

			else: 
				## set to default ray length visualization
				self.ray_geometry.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, self.ray_length * -0.5) * \
													avango.gua.make_rot_mat(-90.0, 1, 0, 0) * \
													avango.gua.make_scale_mat(self.ray_thickness, self.ray_length, self.ray_thickness)

				## update intersection point visualization
				self.intersection_geometry.Tags.value = ["invisible"] # set invisible


			# evtl. drag object
			ManipulationTechnique.dragging(self) 


class VirtualHand(ManipulationTechnique):

	## constructor
	def __init__(self):
		self.super(VirtualHand).__init__()


	def my_constructor( self
					  , MANIPULATION_MANAGER = None                      
					  , PARENT_NODE = None
					  ):

		ManipulationTechnique.my_constructor(self, MANIPULATION_MANAGER = MANIPULATION_MANAGER, PARENT_NODE = PARENT_NODE)


		### further parameters ###  
		self.ray_length = 0.095 # in meter
		#self.intersection_point_size = 0.01 # in meter


		### further resources ###
		_loader = avango.gua.nodes.TriMeshLoader()
		
		## ToDo: init hand nodes here
		self.hand_geometry = _loader.create_geometry_from_file("hand_geometry", "data/objects/hand.obj", avango.gua.LoaderFlags.DEFAULTS)
		self.hand_geometry.Transform.value = avango.gua.make_trans_mat(0.0,0.0,self.ray_length * -0.5) #* \
											 #avango.gua.make_scale_mat(self.ray_length/2, self.ray_length/2, self.ray_length/2)
		self.hand_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
		self.tool_node.Children.value.append(self.hand_geometry)
		

	### callbacks ###
	
	## implement base class function
	def evaluate(self):
	
		# ## ToDo: init behavior here
		# # ...
		if self.enable_flag == True:    
			## calc intersection
			_mf_pick_result = self.MANIPULATION_MANAGER.intersection.calc_pick_result(PICK_MAT = self.hand_geometry.WorldTransform.value, PICK_LENGTH = self.ray_length)
			#print(len(_mf_pick_result.value))

			if len(_mf_pick_result.value) > 0: # intersection found
				self.first_pick_result = _mf_pick_result.value[0] # get first pick result
			
			else: # no intersection found
				self.first_pick_result = None
  
 
			if self.first_pick_result is not None:

				## update hand visualization
				self.hand_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(0.0,1.0,0.0,1.0))

			else: 
				self.hand_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))


			# evtl. drag object
			ManipulationTechnique.dragging(self) 




class GoGo(ManipulationTechnique):

	## constructor
	def __init__(self):
		self.super(GoGo).__init__()


	def my_constructor( self
					  , MANIPULATION_MANAGER = None                      
					  , PARENT_NODE = None
					  ):

		ManipulationTechnique.my_constructor(self, MANIPULATION_MANAGER = MANIPULATION_MANAGER, PARENT_NODE = PARENT_NODE)


		### further parameters ###  
		self.ray_length = 0.095 # in meter
		self.intersection_point_size = 0.01 # in meter

		self.gogo_threshold = 0.35 # in meter


		### further resources ###
		_loader = avango.gua.nodes.TriMeshLoader()
		
		## ToDo: init hand nodes here
		self.hand_geometry = _loader.create_geometry_from_file("hand_geometry", "data/objects/hand.obj", avango.gua.LoaderFlags.DEFAULTS)
		self.hand_geometry.Transform.value = avango.gua.make_trans_mat(0.0,0.0,self.ray_length * -0.5)
		self.hand_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
		self.hand_transform_node = avango.gua.nodes.TransformNode(Name = "hand_node")
		self.hand_transform_node.Children.value.append(self.hand_geometry)
		self.tool_node.Children.value.append(self.hand_transform_node)


	### callbacks ###
	
	# implement base class function
	def evaluate(self):
	
		## ToDo: init behavior here
		# ...

		#idea: transfer function computation -> something with _distance -> hand Transform?
		#input: difference between threshold and hand position
		#output: depth-value (<=threshold -> take input value; >threshold -> upscaled input value)

		## hand position handling
		#compute current arm 'reach/range'
		position_head = self.MANIPULATION_MANAGER.HEAD_NODE.WorldTransform.value.get_translate()[2] #depth-value glasses
		position_pointer = self.pointer_node.WorldTransform.value.get_translate()[2] #depth-value pointer
		_eye_hand_offset = abs(position_head) - abs(position_pointer) #negative value: pointer is behind glasses (or loss of proper tracking??)
		#print(_eye_hand_offset)
		#print("\n")


		if _eye_hand_offset > self.gogo_threshold: #is hand in outer arm range?
			self.gogo_behavior(_eye_hand_offset) # perform non-isomorphic GoGo-behaviour
		
######################### intersection...
		if self.enable_flag == True:    
			## calc intersection
			_mf_pick_result = self.MANIPULATION_MANAGER.intersection.calc_pick_result(PICK_MAT = self.hand_geometry.WorldTransform.value, PICK_LENGTH = self.ray_length)

			if len(_mf_pick_result.value) > 0: # intersection found
				self.first_pick_result = _mf_pick_result.value[0] # get first pick result
			
			else: # no intersection found
				self.first_pick_result = None
  
 
			if self.first_pick_result is not None:
				#_point = self.first_pick_result.WorldPosition.value
				#_distance = (self.tool_node.WorldTransform.value.get_translate() - _point).length()

				# ## update ray length visualization
				# self.ray_geometry.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, _distance * -0.5) * \
				# 									avango.gua.make_rot_mat(-90.0, 1, 0, 0) * \
				# 									avango.gua.make_scale_mat(self.ray_thickness, _distance, self.ray_thickness)
  

				# ## update intersection point visualization
				# self.intersection_geometry.Transform.value = avango.gua.make_trans_mat(0.0,0.0,-_distance) * \
				# 											 avango.gua.make_scale_mat(self.intersection_point_size)
																  
				# self.intersection_geometry.Tags.value = [] # set visible

				## update hand visualization
				self.hand_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(0.0,1.0,0.0,1.0))
			else: 
				self.hand_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))


		###  IS THIS NEEDED??? -> what does it do?
			# evtl. drag object
			ManipulationTechnique.dragging(self) 

	### functions ###
	def gogo_behavior(self, _eye_hand_offset):
		#print("here comes gogo:")
		# compute transfer function

		# apply transformation
	#??? APPLY JUST ON DEPTH-VALUE or on whole ???
		# pass
		#_new_mat = self.sf_mat.value * avango.gua.make_trans_mat(_x, _y, _z)

    	#length_new_mat = (_new_mat.get_translate() - self.sf_mat.value.get_translate()).length()

    	#print(length_new_mat)

    	#Function to use
    	#(0.3)*x^2
    	#self.hand_transform_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, _z)
    	#_x *= length_new_mat *25
    	#_y *= length_new_mat *25
    	#_z *= length_new_mat *25

    	#_new_mat = self.sf_mat.value * avango.gua.make_trans_mat(_x, _y, _z)
    	#self.set_matrix(_new_mat) # apply new input matrix

    	# ## update ray length visualization

    	#One of those must be updated
		# self.tool_nood.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, _distance * -0.5) * \
		_z = (-8) * pow(_eye_hand_offset - self.gogo_threshold,2)
		self.tool_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, _z)
		#self.hand_transform_node.Transform.value

		#Do we need to modify the drag function
		# def start_dragging(self, NODE):          
		# #self.dragged_node = NODE
		# self.dragged_node = NODE.Parent.value # take the group node of the geomtry node
		# self.dragging_offset_mat = avango.gua.make_inverse_mat(self.tool_node.WorldTransform.value) * self.dragged_node.Transform.value # object transformation in pointer coordinate system

  		
		# def stop_dragging(self): 
		# 	self.dragged_node = None
		# 	self.dragging_offset_mat = avango.gua.make_identity_mat()


		# def dragging(self):
		# 	if self.dragged_node is not None: # object to drag
		# 		self.dragged_node.Transform.value = self.tool_node.WorldTransform.value * self.dragging_offset_mat


class Homer(ManipulationTechnique):

	## constructor
	def __init__(self):
		self.super(Homer).__init__()


	def my_constructor( self
					  , MANIPULATION_MANAGER = None                      
					  , PARENT_NODE = None
					  ):

		ManipulationTechnique.my_constructor(self, MANIPULATION_MANAGER = MANIPULATION_MANAGER, PARENT_NODE = PARENT_NODE)


		### further parameters ###  
		self.ray_length = 2.0 # in meter
		self.ray_thickness = 0.005 # in meter
		self.ray_hand_length = 0.095 # in meter
		self.intersection_point_size = 0.01 # in meter
		self.init_eye_hand_offset = 0
		self.init_headset = 0

		self.mode = 0 # 0 = ray-mode; 1 = hand-mode

		### further resources ###
		_loader = avango.gua.nodes.TriMeshLoader()
		
		## ToDo: init ray and hand nodes here
		self.ray_geometry = _loader.create_geometry_from_file("ray_geometry", "data/objects/cylinder.obj", avango.gua.LoaderFlags.DEFAULTS)
		self.ray_geometry.Transform.value = avango.gua.make_trans_mat(0.0,0.0,self.ray_length * -0.5) * \
											avango.gua.make_rot_mat(-90.0,1,0,0) * \
											avango.gua.make_scale_mat(self.ray_thickness, self.ray_length, self.ray_thickness)
		self.ray_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
		self.tool_node.Children.value.append(self.ray_geometry)

		self.intersection_geometry = _loader.create_geometry_from_file("intersection_geometry", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS)
		#self.intersection_geometry.Tags.value = ["invisible"] # set geometry invisible
		self.intersection_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
		self.tool_node.Children.value.append(self.intersection_geometry)
		
		## ToDo: init hand nodes here
		self.hand_geometry = _loader.create_geometry_from_file("hand_geometry", "data/objects/hand.obj", avango.gua.LoaderFlags.DEFAULTS)
		#self.hand_geometry.Tags.value = ["invisible"] # set geometry invisible
		self.hand_geometry.Transform.value = avango.gua.make_trans_mat(0.0,0.0,self.ray_hand_length * -0.5) #* \
											 #avango.gua.make_scale_mat(self.ray_length/2, self.ray_length/2, self.ray_length/2)
		self.hand_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(0.0,1.0,0.0,1.0))
		#self.tool_node.Children.value.append(self.hand_geometry)
		self.tool_node.Children.value.append(self.hand_geometry)




	### callbacks ###
	
	# implement base class function
	def evaluate(self):
	
		if self.enable_flag == True:  
			if self.mode == 0: # ray submode
				self.ray_mode()
				
			elif self.mode == 1: # hand submode
				self.hand_mode()

			# evtl. drag object
			ManipulationTechnique.dragging(self)


	### functions ###
	def set_homer_mode(self, INT):
		self.mode = INT

		## ToDo: toggle submode visibilities
		# ...
		
		if self.mode == 0: # ray submode
			pass
			#self.intersection_geometry.Tags.value = [] # set visible
			self.ray_geometry.Tags.value = []
			self.hand_geometry.Tags.value = ["invisible"]
		
		elif self.mode == 1: # hand submode
			self.hand_geometry.Tags.value = []
			self.ray_geometry.Tags.value = ["invisible"]
			self.intersection_geometry.Tags.value = ["invisible"] # set invisible

	
	def ray_mode(self):

		## ToDo: init ray submode behavior here
		if self.enable_flag == True:    
			## calc intersection
			_mf_pick_result = self.MANIPULATION_MANAGER.intersection.calc_pick_result(PICK_MAT = self.tool_node.WorldTransform.value, PICK_LENGTH = self.ray_length)
			#print(len(_mf_pick_result.value))
			
			if len(_mf_pick_result.value) > 0: # intersection found
				self.first_pick_result = _mf_pick_result.value[0] # get first pick result
			
			else: # no intersection found
				self.first_pick_result = None
  
 
			if self.first_pick_result is not None:
				#print("Grab 1")
				_point = self.first_pick_result.WorldPosition.value
				_distance = (self.tool_node.WorldTransform.value.get_translate() - _point).length()
				
				## update ray length visualization
				self.ray_geometry.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, _distance * -0.5) * \
													avango.gua.make_rot_mat(-90.0, 1, 0, 0) * \
													avango.gua.make_scale_mat(self.ray_thickness, _distance, self.ray_thickness)
  

				## update intersection point visualization
				self.intersection_geometry.Transform.value = avango.gua.make_trans_mat(0.0,0.0,-_distance) * \
															 avango.gua.make_scale_mat(self.intersection_point_size)
																  
				self.intersection_geometry.Tags.value = [] # set visible

			else: 
				## set to default ray length visualization
				self.ray_geometry.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, self.ray_length * -0.5) * \
													avango.gua.make_rot_mat(-90.0, 1, 0, 0) * \
													avango.gua.make_scale_mat(self.ray_thickness, self.ray_length, self.ray_thickness)

				## update intersection point visualization
				self.intersection_geometry.Tags.value = ["invisible"] # set visible				
	

	def hand_mode(self):    
		# ToDo: init hand submode behavior here
		self.hand_geometry.Tags.value = [] # set visible
		_mf_pick_result = self.MANIPULATION_MANAGER.intersection.calc_pick_result(PICK_MAT = self.tool_node.WorldTransform.value, PICK_LENGTH = self.ray_length)

		if len(_mf_pick_result.value) > 0: # intersection found
		 	self.first_pick_result = _mf_pick_result.value[0] # get first pick result
		else: # no intersection found
		 	self.first_pick_result = None

		if self.first_pick_result is not None:
		 	_point = self.first_pick_result.WorldPosition.value
		 	_distance = (self.tool_node.WorldTransform.value.get_translate() - _point).length()
				
				## update ray length visualization
		 	#self.ray_geometry.Tags.value = ["invisible"]
		 	#self.intersection_geometry.Tags.value = ["invisible"] # set invisible
		# 		## update intersection point visualization
		 	self.hand_geometry.Transform.value = avango.gua.make_trans_mat(0.0,0.0,-_distance + self.ray_hand_length/2)
		 	self.hand_geometry.Tags.value = [] # set visible

		 	#Implementation
		 	#position_head = self.MANIPULATION_MANAGER.HEAD_NODE.WorldTransform.value.get_translate()[2] #depth-value glasses
			#position_pointer = self.pointer_node.WorldTransform.value.get_translate()[2] #depth-value pointer

			#First distance option
		 	#position_head = abs(self.MANIPULATION_MANAGER.HEAD_NODE.WorldTransform.value.get_translate()[2])

		 	#Second option
		 	position_head = self.init_headset

		 	_current = self.calc_offset()

		 	new_distance = (position_head * (_current/self.init_eye_hand_offset)) - position_head
		 	print(new_distance)
		 	#_z = (-8) * pow(_eye_hand_offset - self.init_eye_hand_offset,2)
		 	self.tool_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, -new_distance)
		else:
			pass 
		### set to default ray length visualization
		 	# self.hand_geometry.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, self.ray_length * -0.5) * \
		 	# 									avango.gua.make_rot_mat(-90.0, 1, 0, 0) * \
		 	# 									avango.gua.make_scale_mat(self.ray_thickness, self.ray_length, self.ray_thickness)
		# 		## update intersection point visualization
			#self.hand_geometry.Tags.value = [] # set visible
			#self.intersection_geometry.Tags.value = ["invisible"] # set invisible

	def calc_offset(self):  

		## ToDo: evtl. calc necessary offsets and parameters here for switch between ray and hand mode
		# ...

		position_head = self.MANIPULATION_MANAGER.HEAD_NODE.WorldTransform.value.get_translate()[2] #depth-value glasses
		position_pointer = self.pointer_node.WorldTransform.value.get_translate()[2] #depth-value pointer
		return abs(position_head) - abs(position_pointer) #negative value: pointer is behind glasses (or loss of proper tracking??)
		  
	
	## extend respective base-class function
	def start_dragging(self, NODE):
		self.init_eye_hand_offset = self.calc_offset()
		self.init_headset = abs(self.MANIPULATION_MANAGER.HEAD_NODE.WorldTransform.value.get_translate()[2])
		self.set_homer_mode(1) # switch to hand submode

		ManipulationTechnique.start_dragging(self, NODE) # call base class function
		#print("start dragging")
		# ToDo: evtl. override dragging offset here
		# ...
		


	## extend respective base-class function
	def stop_dragging(self):
		self.set_homer_mode(0) # switch to ray submode
		ManipulationTechnique.stop_dragging(self) # call base class function



	## extend respective base-class function
	def enable(self, FLAG):
		ManipulationTechnique.enable(self, FLAG) # call base class function

		if self.enable_flag == True: 
			self.set_homer_mode(0) # switch to ray submode
			#print("enable")


