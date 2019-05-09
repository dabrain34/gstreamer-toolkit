# Set up basic variables:
CC = gcc
CFLAGS = -Wall
LDFLAGS =


# Name of executable target:
EXECUTABLES = gst_buffer_probe gst_ogg_player gst_typefind

GST_FLAGS += `pkg-config --cflags --libs gstreamer-1.0`


all: $(EXECUTABLES)

gst_buffer_probe:
	$(CC) $(CFLAGS) $@.c -o $@ $(GST_FLAGS)

gst_typefind:
	$(CC) $(CFLAGS) $@.c -o $@ $(GST_FLAGS)

gst_ogg_player:
	$(CC) $(CFLAGS) $@.c -o $@ $(GST_FLAGS)

clean:
	rm $(EXECUTABLES)

