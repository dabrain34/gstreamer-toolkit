easy_c_args = []
fs = import('fs')
if get_option('default_library') == 'static'
  gst_full_dep = dependency('gstreamer-full-1.0')
  if fs.exists('scripts/gstinitstaticplugins.h')
    easy_c_args += ['-DGST_STATIC_COMPILATION']
  endif
else
  gst_full_dep = dependency('gstreamer-1.0',
    fallback : ['gstreamer', 'gst_dep'])
endif

executable('easy-play',
  'src/easy_play.c',
  install: true,
  dependencies : [gst_full_dep],
  c_args: easy_c_args
)

executable('easy-inspect',
  'src/easy_inspect.c',
  install: true,
  dependencies : [gst_full_dep],
  c_args: easy_c_args
)
