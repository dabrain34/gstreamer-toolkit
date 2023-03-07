easy_c_args = []
fs = import('fs')


executable('easy-play',
  'src/easy_play.c',
  install: true,
  dependencies : [gstreamer_full_dep],
  c_args: easy_c_args
)

executable('easy-inspect',
  'src/easy_inspect.c',
  install: true,
  dependencies : [gstreamer_full_dep],
  c_args: easy_c_args
)
