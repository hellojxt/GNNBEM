# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ffat_map.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0e\x66\x66\x61t_map.proto\x12\x08\x66\x66\x61t_map\"\x13\n\x03vec\x12\x0c\n\x04item\x18\x01 \x03(\x01\"\"\n\x03mat\x12\x1b\n\x04item\x18\x01 \x03(\x0b\x32\r.ffat_map.vec\"\x15\n\x05vec_i\x12\x0c\n\x04item\x18\x01 \x03(\x05\"&\n\x05mat_i\x12\x1d\n\x04item\x18\x01 \x03(\x0b\x32\x0f.ffat_map.vec_i\"\xe9\x01\n\x0c\x66\x66\x61t_map_t_1\x12\x10\n\x08\x63\x65llsize\x18\x01 \x01(\x01\x12!\n\nlowcorners\x18\x02 \x01(\x0b\x32\r.ffat_map.mat\x12#\n\nn_elements\x18\x03 \x01(\x0b\x32\x0f.ffat_map.mat_i\x12 \n\x07strides\x18\x04 \x01(\x0b\x32\x0f.ffat_map.vec_i\x12\x1d\n\x06\x63\x65nter\x18\x05 \x01(\x0b\x32\r.ffat_map.vec\x12\x1e\n\x07\x62\x62oxlow\x18\x06 \x01(\x0b\x32\r.ffat_map.vec\x12\x1e\n\x07\x62\x62oxtop\x18\x07 \x01(\x0b\x32\r.ffat_map.vec\"\xa3\x01\n\x0c\x66\x66\x61t_map_t_3\x12\t\n\x01k\x18\x01 \x01(\x01\x12\x1d\n\x06\x63\x65nter\x18\x02 \x01(\x0b\x32\r.ffat_map.vec\x12&\n\x06shells\x18\x03 \x01(\x0b\x32\x16.ffat_map.ffat_map_t_1\x12\x15\n\ris_compressed\x18\x04 \x01(\x08\x12\x1a\n\x03psi\x18\x05 \x01(\x0b\x32\r.ffat_map.mat\x12\x0e\n\x06modeid\x18\x06 \x01(\x05\"6\n\x0f\x66\x66\x61t_map_double\x12#\n\x03map\x18\x01 \x01(\x0b\x32\x16.ffat_map.ffat_map_t_3b\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'ffat_map_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _VEC._serialized_start=28
  _VEC._serialized_end=47
  _MAT._serialized_start=49
  _MAT._serialized_end=83
  _VEC_I._serialized_start=85
  _VEC_I._serialized_end=106
  _MAT_I._serialized_start=108
  _MAT_I._serialized_end=146
  _FFAT_MAP_T_1._serialized_start=149
  _FFAT_MAP_T_1._serialized_end=382
  _FFAT_MAP_T_3._serialized_start=385
  _FFAT_MAP_T_3._serialized_end=548
  _FFAT_MAP_DOUBLE._serialized_start=550
  _FFAT_MAP_DOUBLE._serialized_end=604
# @@protoc_insertion_point(module_scope)
