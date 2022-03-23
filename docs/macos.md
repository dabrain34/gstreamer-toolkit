# macos build

meson builddir -Dexamples=disabled -Dgst-plugins-bad:openexr=disabled -Dintrospection=disabled \
               -Dgst-examples=disabled -Dgst-plugins-base:pango=enabled -Dgst-devtools:cairo=disabled \
               -Dforce_fallback_for=pcre -Dbackend=ninja -Dgpl=enabled -Dgst-plugins-base:tests=disabled \
               -Dtests=disabled
