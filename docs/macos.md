# macos build

meson builddir   -Dintrospection=disabled \
               -Dforce_fallback_for=pcre -Dbackend=ninja -Dgpl=enabled

