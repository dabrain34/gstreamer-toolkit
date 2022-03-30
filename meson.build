project('gst-toolkit', 'c', 'cpp',
  version: '0.1',
  meson_version: '>=0.54.0',
)

if get_option('gstreamer-full')
  gst_full_dep = dependency('gstreamer-full-1.0', static: get_option('default_library') == 'static', required: false)
  if not gst_full_dep.found()
    gst_full_dep = dependency('gstreamer-1.0',
      fallback : ['gstreamer', 'gst_dep'])
  endif
else
  gst_full_dep = dependency('gstreamer-1.0',
    fallback : ['gstreamer', 'gst_dep'])
endif

pkg = import('pkgconfig')

if not get_option('tools').disabled()
  subdir('tools')
endif

tools = ['gst_ogg_player', 'gst_buffer_probe', 'gst_typefind']

foreach tool : tools
  exe_name = '@0@'.format(tool)
  src_file = 'src/@0@.c'.format(tool)

  executable(exe_name,
    src_file,
    install: true,
    dependencies : [gst_full_dep],
  )
endforeach

