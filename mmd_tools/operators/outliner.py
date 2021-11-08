# -*- coding: utf-8 -*-

import bpy
from bpy.ops import outliner

from mmd_tools import register_wrap
import mmd_tools.core.model as mmd_model


@register_wrap
class SimpleOperator(bpy.types.Operator):
    bl_idname = 'mmd_tools.make_object_id_data_local'
    bl_label = 'Make Object ID Data Local'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.area.type == 'OUTLINER'
            and context.object.type == 'EMPTY'
            and context.object.override_library is not None
        )

    def execute(self, context):
        # bpy.ops.object.make_override_library()

        root_object = mmd_model.Model.findRoot(context.active_object)
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

        # select_children(model.rigidGroupObject())
        select_children(model.jointGroupObject())
        # select_children(model.temporaryGroupObject())

        # bpy.context.view_layer.update()
        outliner_context = context.copy()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        bpy.ops.outliner.id_operation(outliner_context, type='LOCAL')

        # reset_object_visibilities()

        # bpy.ops.outliner.select_walk(outliner_context, direction='LEFT')
        # bpy.ops.outliner.select_all(outliner_context, action='DESELECT')
        # bpy.ops.outliner.hide(outliner_context)

        return {'FINISHED'}
