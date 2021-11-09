# -*- coding: utf-8 -*-

import bpy
from bpy.ops import outliner

from mmd_tools import register_wrap
import mmd_tools.core.model as mmd_model


STATE_INIT = 'STATE_INIT'
STATE_MAKE_OVERRIDE_LIBRARY_WAITING = 'STATE_MAKE_OVERRIDE_LIBRARY_WAITING'
STATE_MAKE_OVERRIDE_LIBRARY_RUNNING = 'STATE_MAKE_OVERRIDE_LIBRARY_RUNNING'
STATE_MAKE_LOCAL_ID_DATA_WAITING = 'STATE_MAKE_LOCAL_ID_DATA_WAITING'
STATE_MAKE_LOCAL_ID_DATA_RUNNING = 'STATE_MAKE_LOCAL_ID_DATA_RUNNING'
STATE_COLLAPSE_LEAF_WAITING = 'STATE_COLLAPSE_LEAF_WAITING'
STATE_COLLAPSE_LEAF_RUNNING = 'STATE_COLLAPSE_LEAF_RUNNING'
STATE_FINISHED = 'STATE_FINISHED'


@register_wrap
class SimpleOperator(bpy.types.Operator):
    bl_idname = 'mmd_tools.make_object_id_data_local'
    bl_label = 'Make Object ID Data Local'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def __poll(cls, context):
        return (
            context.area.type == 'OUTLINER'
            and context.object.type == 'EMPTY'
            and context.object.override_library is not None
        )

    _timer = None
    _state = STATE_INIT

    def __init__(self):
        pass

    def __del__(self):
        if self._timer is not None:
            bpy.context.window_manager.event_timer_remove(self._timer)
            self._timer = None

    def modal(self, context, event):
        if 'MOUSEMOVE' in event.type:
            return {'RUNNING_MODAL'}

        if 'WHEEL' in event.type:
            return {'RUNNING_MODAL'}

        print('modal', event.type, self._state)

        if event.type != 'TIMER':
            return {'RUNNING_MODAL'}

        if self._state == STATE_INIT:
            return {'CANCELLED'}

        if self._state == STATE_MAKE_OVERRIDE_LIBRARY_WAITING:
            self._state = STATE_MAKE_OVERRIDE_LIBRARY_RUNNING
            try:
                bpy.ops.object.make_override_library()
            finally:
                self._state = STATE_MAKE_LOCAL_ID_DATA_WAITING
            return {'RUNNING_MODAL'}

        if self._state == STATE_MAKE_OVERRIDE_LIBRARY_RUNNING:
            return {'RUNNING_MODAL'}

        if self._state == STATE_MAKE_LOCAL_ID_DATA_WAITING:
            self._state = STATE_MAKE_LOCAL_ID_DATA_RUNNING
            try:
                self.__execute(context)
            finally:
                self._state = STATE_COLLAPSE_LEAF_WAITING
            return {'RUNNING_MODAL'}

        if self._state == STATE_MAKE_LOCAL_ID_DATA_RUNNING:
            return {'RUNNING_MODAL'}

        if self._state == STATE_COLLAPSE_LEAF_WAITING:
            self._state = STATE_COLLAPSE_LEAF_RUNNING
            try:
                bpy.ops.outliner.select_walk('INVOKE_DEFAULT', direction='LEFT')
                bpy.ops.outliner.select_walk('INVOKE_DEFAULT', direction='LEFT')
                bpy.ops.outliner.select_walk('INVOKE_DEFAULT', direction='LEFT')
            finally:
                self._state = STATE_FINISHED
            return {'RUNNING_MODAL'}

        if self._state == STATE_FINISHED:
            return {'FINISHED'}

        return {'CANCELLED'}

    def invoke(self, context, event):
        print('invoke', event.type)
        self._state = STATE_MAKE_OVERRIDE_LIBRARY_WAITING
        context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        print('execute')
        print('start: bpy.ops.object.make_override_library')
        bpy.ops.object.make_override_library()
        print('end: bpy.ops.object.make_override_library')
        return {'FINISHED'}

    def __execute(self, context):
        # bpy.ops.object.make_override_library()

        root_object = mmd_model.Model.findRoot(context.selected_objects[0])
        model = mmd_model.Model(root_object)

        object_visibilities = dict()

        def force_show_object(obj):
            object_visibilities[obj.name] = {
                'hide': obj.hide_get(),
                'hide_select': obj.hide_select,
                'hide_viewport': obj.hide_viewport,
            }
            obj.hide_select = False
            obj.hide_viewport = False
            obj.hide_set(False)

        def reset_object_visibilities():
            for object_name, visibility in object_visibilities.items():
                obj = bpy.data.objects[object_name]
                obj.hide_set(visibility['hide'])
                obj.hide_viewport = visibility['hide_viewport']
                obj.hide_select = visibility['hide_select']

        def select_children(parent):
            force_show_object(parent)
            parent.select_set(True)

            context.view_layer.objects.active = parent
            bpy.ops.outliner.show_active()

            for obj in parent.children:
                if not obj.override_library:
                    continue

                print(f'id_operation: {obj.name}')
                force_show_object(obj)
                obj.select_set(True)

            context.view_layer.objects.active = obj
            bpy.ops.outliner.show_active()

        select_children(model.rigidGroupObject())
        select_children(model.jointGroupObject())
        select_children(model.temporaryGroupObject())

        # bpy.context.view_layer.update()
        outliner_context = context.copy()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        bpy.ops.outliner.id_operation(outliner_context, type='LOCAL')

        # reset_object_visibilities()

        # bpy.ops.outliner.select_walk(outliner_context, direction='LEFT')
        # bpy.ops.outliner.select_all(outliner_context, action='DESELECT')
        # bpy.ops.outliner.hide(outliner_context)

        return {'FINISHED'}
