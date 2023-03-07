project('gst-toolkit', 'c', 'cpp',
  version: '0.1',
  meson_version: '>=0.54.0',
)


gstreamer_full_dep = dependency('gstreamer-full-1.0', static: true, fallback: ['gstreamer-1.0'], required :false)
if not gstreamer_full_dep.found()
    gstreamer_full_dep = dependency('gstreamer-1.0',
      fallback : ['gstreamer', 'gst_dep'])
endif


pkg = import('pkgconfig')


subdir('tools')


tools = ['gst_ogg_player', 'gst_buffer_probe', 'gst_typefind']

foreach tool : tools
  exe_name = '@0@'.format(tool)
  src_file = 'src/@0@.c'.format(tool)

  executable(exe_name,
    src_file,
    install: true,
    dependencies : [gstreamer_full_dep],
  )
endforeach

