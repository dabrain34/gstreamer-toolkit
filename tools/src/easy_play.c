#include <gst/gst.h>
#ifdef GST_STATIC_COMPILATION
#  include <gst/gstinitstaticplugins.h>
#endif
#ifdef G_OS_UNIX
#include <glib-unix.h>
#endif

typedef struct _GstEasyPlayer
{
  GMainLoop *loop;
  GstElement * pipeline;
  guint signal_watch_intr_id;
  GIOChannel *io_stdin;
  gboolean interactive;
  GstState pending_state;
  GstState state;
  gboolean auto_play;
  gboolean buffering;
  gulong deep_notify_id;

} GstEasyPlayer;

static gboolean sLog = TRUE;

#define LOG(FMT, ARGS...) do { \
    if (sLog) \
        g_print(FMT "\n", ## ARGS); \
    } while (0)

void
quit_app (GstEasyPlayer * thiz)
{
  if (thiz->loop)
    g_main_loop_quit (thiz->loop);
}

#if defined(G_OS_UNIX) || defined(G_OS_WIN32)
/* As the interrupt handler is dispatched from GMainContext as a GSourceFunc
 * handler, we can react to this by posting a message. */
static gboolean
intr_handler (gpointer user_data)
{
  GstEasyPlayer *thiz = (GstEasyPlayer *) user_data;

  LOG ("handling interrupt.");
  quit_app (thiz);
  /* remove signal handler */
  thiz->signal_watch_intr_id = 0;

  return G_SOURCE_REMOVE;
}
#endif

gboolean
set_state (GstEasyPlayer * thiz, GstState state)
{
  gboolean res = TRUE;
  GstStateChangeReturn ret;

  g_assert (thiz != NULL);

  ret = gst_element_set_state (thiz->pipeline, state);

  switch (ret) {
    case GST_STATE_CHANGE_FAILURE:
      LOG ("ERROR: %s doesn't want to pause.",
          GST_ELEMENT_NAME (thiz->pipeline));
      res = FALSE;
      break;
    case GST_STATE_CHANGE_NO_PREROLL:
      break;
    case GST_STATE_CHANGE_ASYNC:
      LOG ("%s is PREROLLING ...", GST_ELEMENT_NAME (thiz->pipeline));
      break;
      /* fallthrough */
    case GST_STATE_CHANGE_SUCCESS:
      if (thiz->state == GST_STATE_PAUSED)
        LOG ("%s is PREROLLED ...", GST_ELEMENT_NAME (thiz->pipeline));
      break;
  }
  return res;
}

static void
change_state (GstEasyPlayer * thiz, GstState state)
{
  if (thiz->state == thiz->pending_state)
    return;

  thiz->state = state;
  LOG ("player is %s", gst_element_state_get_name (state));
  switch (state) {
    case GST_STATE_READY:
        set_state (thiz, GST_STATE_PAUSED);
      break;
    case GST_STATE_PAUSED:
        set_state (thiz, GST_STATE_PLAYING);
      break;
    case GST_STATE_PLAYING:
      break;
    default:
      break;
  }
}


static gboolean
message_cb (GstBus * bus, GstMessage * message, gpointer user_data)
{
  GstEasyPlayer *thiz = (GstEasyPlayer *) user_data;
  GST_DEBUG_OBJECT (thiz, "Received new message %s from %s",
      GST_MESSAGE_TYPE_NAME (message), GST_OBJECT_NAME (message->src));
  switch (GST_MESSAGE_TYPE (message)) {
    case GST_MESSAGE_ERROR:{
      GError *err = NULL;
      gchar *name, *debug = NULL;

      name = gst_object_get_path_string (message->src);
      gst_message_parse_error (message, &err, &debug);

      GST_ERROR_OBJECT (thiz, "ERROR: from element %s: %s\n", name,
          err->message);
      if (debug != NULL)
        GST_ERROR_OBJECT (thiz, "Additional debug info:%s", debug);

      g_error_free (err);
      g_free (debug);
      g_free (name);

      quit_app(thiz);
      break;
    }
    case GST_MESSAGE_WARNING:{
      GError *err = NULL;
      gchar *name, *debug = NULL;

      name = gst_object_get_path_string (message->src);
      gst_message_parse_warning (message, &err, &debug);

      GST_WARNING_OBJECT (thiz, "ERROR: from element %s: %s\n", name,
          err->message);
      if (debug != NULL)
        GST_WARNING_OBJECT (thiz, "Additional debug info:\n%s\n", debug);

      g_error_free (err);
      g_free (debug);
      g_free (name);
      break;
    }
    case GST_MESSAGE_EOS:
      LOG("Received EOS, quit");
      quit_app (thiz);
      break;

    case GST_MESSAGE_STATE_CHANGED:
    {
      GstState old, new, pending;
      if (GST_MESSAGE_SRC (message) == GST_OBJECT_CAST (thiz->pipeline)) {
        gst_message_parse_state_changed (message, &old, &new, &pending);
        thiz->state = new;
        change_state (thiz, new);
      }
      break;
    }
    case GST_MESSAGE_BUFFERING:{
      gint percent;

      gst_message_parse_buffering (message, &percent);
      LOG ("buffering  %d%% ", percent);


      if (percent == 100) {
        /* a 100% message means buffering is done */
        thiz->buffering = FALSE;
        /* if the desired state is playing, go back */
        if (thiz->state == GST_STATE_PLAYING) {
          LOG ("Done buffering, setting pipeline to PLAYING ...");
          gst_element_set_state (thiz->pipeline, GST_STATE_PLAYING);
        }
      } else {
        /* buffering busy */
        if (!thiz->buffering && thiz->state == GST_STATE_PLAYING) {
          /* we were not buffering but PLAYING, PAUSE  the pipeline. */
          LOG ("Buffering, setting pipeline to PAUSED ...");
          gst_element_set_state (thiz->pipeline, GST_STATE_PAUSED);
        }
        thiz->buffering = TRUE;
      }
      break;
    }
    default:
      break;
  }

  return TRUE;
}

int
main (int argc, char *argv[])
{
  GOptionContext *ctx;
  GError *err = NULL;
  gchar* parsing_line = NULL;
  gchar** elements = NULL;
  GstElement * bin;
  GstEasyPlayer * thiz;
  GstBus * bus;

  GOptionEntry options[] = {
    {G_OPTION_REMAINING, 0, 0, G_OPTION_ARG_FILENAME_ARRAY, &elements, NULL},
    {NULL}
  };
  ctx = g_option_context_new ("elements ...");
  g_option_context_add_main_entries (ctx, options, NULL);
  g_option_context_add_group (ctx, gst_init_get_option_group ());
  if (!g_option_context_parse (ctx, &argc, &argv, &err)) {
    g_print ("Error initializing: %s\n", GST_STR_NULL (err->message));
    g_clear_error (&err);
    g_option_context_free (ctx);
    return 1;
  }
  g_option_context_free (ctx);

  gst_init (&argc, &argv);

#ifdef GST_STATIC_COMPILATION
  gst_init_static_plugins();
#endif
  if (!elements)
    return 0;

  thiz = g_new0 (GstEasyPlayer, 1);

  parsing_line = g_strjoinv (" ", elements);
  g_print("line: %s\n",parsing_line);
  bin = gst_parse_launch_full (parsing_line, NULL, GST_PARSE_FLAG_NONE,
      &err);
  thiz->pipeline = gst_pipeline_new (NULL);
  thiz->state = GST_STATE_NULL;
  gst_bin_add (GST_BIN (thiz->pipeline), bin);

  bus = gst_pipeline_get_bus (GST_PIPELINE (thiz->pipeline));
  g_signal_connect (G_OBJECT (bus), "message", G_CALLBACK (message_cb), thiz);
  gst_bus_add_signal_watch (bus);
  gst_object_unref (GST_OBJECT (bus));
  thiz->deep_notify_id =
        gst_element_add_property_deep_notify_watch (thiz->pipeline, NULL,
        TRUE);
  thiz->loop = g_main_loop_new (NULL, FALSE);
#ifdef G_OS_UNIX
  thiz->signal_watch_intr_id =
      g_unix_signal_add (SIGINT, (GSourceFunc) intr_handler, thiz);
#endif

  thiz->state = GST_STATE_NULL;
  thiz->pending_state = GST_STATE_PLAYING;
  set_state (thiz, thiz->pending_state);

  g_main_loop_run (thiz->loop);

  bus = gst_pipeline_get_bus (GST_PIPELINE(thiz->pipeline));
  gst_bus_remove_signal_watch (bus);

  gst_element_set_state (thiz->pipeline, GST_STATE_NULL);
  gst_object_unref (thiz->pipeline);
  g_free (thiz);

  return 0;
}
