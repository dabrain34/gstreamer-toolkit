project('gst-toolkit', 'c', 'cpp',
  version: '0.1',
  meson_version: '>=0.54.0',
)

pkg = import('pkgconfig')

if not get_option('tools').disabled()
  subdir('tools')
endif


