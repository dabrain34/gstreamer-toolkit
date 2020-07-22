#include "gst/gst.h"
#ifdef GST_STATIC_COMPILATION
#   include "gst/gstinitstaticplugins.h"
#endif

static void display_elements ()
{
  GList *plugins;
  GList  *p;
  GList *features;
  GList *f;

  plugins = gst_registry_get_plugin_list (gst_registry_get ());
  for ( p =plugins; p; p = p->next) {
      GstPlugin * plugin;
      plugin = (GstPlugin *) (p->data);
      if (GST_OBJECT_FLAG_IS_SET (plugin, GST_PLUGIN_FLAG_BLACKLISTED)) {
        continue;
      }
      features =
              gst_registry_get_feature_list_by_plugin (gst_registry_get (),
              gst_plugin_get_name (plugin));
      for (f = features; f; f = f->next) {
        GstPluginFeature *feature = GST_PLUGIN_FEATURE(f->data);
        if (GST_IS_ELEMENT_FACTORY (feature)) {
            GstElementFactory *factory;
            factory = GST_ELEMENT_FACTORY (feature);
            g_print ("%s: %s: %s\n",
                          gst_plugin_get_name (plugin), GST_OBJECT_NAME (factory),
                          gst_element_factory_get_metadata (factory, GST_ELEMENT_METADATA_LONGNAME));
        }

      }
  }
}

int main(int argc, char *argv[])
{
  gst_init (&argc, &argv);

#ifdef GST_STATIC_COMPILATION
  gst_init_static_plugins();
#endif
  display_elements();
}
