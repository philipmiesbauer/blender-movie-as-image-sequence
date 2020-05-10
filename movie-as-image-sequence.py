bl_info = {
    "name": "Open as Image Sequence",
    "author": "Philip Miesbauer",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "Movie Clip Editor > Clip > Open Clip as Image Sequence",
    "warning": "ffmpeg needs to be installed on your system",
    "description": "Allows to import a movie clip as image sequence directly",
    "wiki_url": "",
    "category": "Import-Export",
    "support": "TESTING"
}


import bpy  # noqa: E402
from bpy.types import Operator, AddonPreferences  # noqa: E402
from bpy.props import StringProperty  # noqa: E402
from os.path import isfile, join, splitext, basename  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402


def is_exe(file_path):
    return os.path.isfile(file_path) and os.access(file_path, os.X_OK)


def which(program, fail=True):
    """ Sort of replicates the `which` utility.
    """
    if sys.platform == 'win32':
        program = program + '.exe'
    locations = [os.path.join(path, program)
                 for path in os.environ["PATH"].split(os.pathsep)]
    found = [loc for loc in locations if is_exe(loc)]

    if not found:
        if not fail:
            return False
        else:
            return None
    else:
        return found[0]


class OpenImageSequenceAddonPreferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    ffmpeg_path = "Point to location of ffmpeg executable"
    exec_path = which('ffmpeg')
    if exec_path is not None:
        ffmpeg_path = exec_path

    ffmpeg_exec_path: StringProperty(
        name="'ffmpeg' executable",
        subtype='FILE_PATH',
        default=ffmpeg_path
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "ffmpeg_exec_path")


class OpenAsImageSequence(Operator):
    """Open Clip directly as image sequence"""
    bl_idname = "object.movie_as_image_sequence"
    bl_label = "Open Clip as Image Sequence"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(
        default="*.mpg;*.mpeg;*.mp4;*.avi;*.mov;*.dv;",
        options={'HIDDEN'},
        )
    filepath: StringProperty(
            name="Clip Path",
            description="Clip to be opened as image sequence",
            maxlen=1024,
            subtype='FILE_PATH',
            )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        preferences = context.preferences
        prefs = preferences.addons[__name__].preferences

        wm = bpy.context.window_manager

        import subprocess

        # Create folder if it doesn't already exist
        (dir_name, extention) = splitext(self.filepath)
        if not os.path.isdir(dir_name):
            os.mkdir(dir_name)
        # progress from [0 - 100]
        wm.progress_begin(0, 2)
        wm.progress_update(1)
        process = subprocess.Popen([prefs.ffmpeg_exec_path,
                                    '-y',
                                    '-i',
                                    self.filepath,
                                    join(dir_name,
                                         "frame_%04d.png")])
        while process.poll() is None:
            wm.progress_update(1)
        image_sequence = [{"name": f} for f in os.listdir(dir_name)
                          if isfile(join(dir_name, f))]
        bpy.data.movieclips["frame_0001.png"].name = basename(dir_name)

        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = len(image_sequence)
        bpy.context.scene.frame_step = 1

        wm.progress_end()

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(OpenAsImageSequence.bl_idname)


# Registration
def register():
    bpy.utils.register_class(OpenImageSequenceAddonPreferences)
    bpy.utils.register_class(OpenAsImageSequence)
    bpy.types.CLIP_MT_clip.append(menu_func)


def unregister():
    bpy.types.CLIP_MT_clip.remove(menu_func)
    bpy.utils.unregister_class(OpenImageSequenceAddonPreferences)
    bpy.utils.unregister_class(OpenAsImageSequence)


if __name__ == "__main__":
    register()
