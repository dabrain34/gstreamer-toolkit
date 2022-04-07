# RTP

## RTP simple

### JPEG Source

```
$ gst-launch-1.0 udpsrc port=7001 ! application/x-rtp,encoding-name=JPEG ! rtpjpegdepay ! jpegdec ! autovideosink
```

### JPEG sink

```
$ gst-launch-1.0 videotestsrc is-live=true ! jpegenc ! rtpjpegpay  ! udpsink  host=127.0.0.1 port=7001
```

## SRTP

### ALAW src
```
gst-launch-1.0 audiotestsrc ! alawenc ! rtppcmapay ! 'application/x-rtp, payload=(int)8, ssrc=(uint)1356955624' ! srtpenc key="012345678901234567890123456789012345678901234567890123456789" ! udpsink port=5004 host=127.0.0.1
```

### ALAW Sink

```
gst-launch-1.0 udpsrc port=5004 caps='application/x-srtp, payload=(int)8, ssrc=(uint)1356955624, srtp-key=(buffer)012345678901234567890123456789012345678901234567890123456789, srtp-cipher=(string)aes-128-icm, srtp-auth=(string)hmac-sha1-80, srtcp-cipher=(string)aes-128-icm, srtcp-auth=(string)hmac-sha1-80' !  srtpdec ! rtppcmadepay ! alawdec ! pulsesink
```

### AMR src
```
gst-launch-1.0 audiotestsrc ! amrnbenc ! rtpamrpay ! 'application/x-rtp, payload=(int)96, ssrc=(uint)1356955624' ! srtpenc key="012345678901234567890123456789012345678901234567890123456789" ! udpsink port=5004 host=127.0.0.1
```

### AMR sink
```
gst-launch-1.0 udpsrc caps='application/x-srtp,media=(string)audio,clock-rate=(int)8000,encoding-name=(string)AMR,encoding-params=(string)1,octet-align=(string)1, ssrc=(uint)1356955624, srtp-key=(buffer)012345678901234567890123456789012345678901234567890123456789, srtp-cipher=(string)aes-128-icm, srtp-auth=(string)hmac-sha1-80, srtcp-cipher=(string)aes-128-icm, srtcp-auth=(string)hmac-sha1-80'  port=5004 ! srtpdec name=dec_rtp ! rtpamrdepay ! amrnbdec ! pulsesink
```

## RTPbin

### AMR Source
```
gst-launch-1.0 rtpbin name=rtpbin \
               audiotestsrc ! amrnbenc ! rtpamrpay ! rtpbin.send_rtp_sink_1 \
               rtpbin.send_rtp_src_1  ! udpsink host=127.0.0.1 port=5002 \
               rtpbin.send_rtcp_src_1 !  udpsink host=127.0.0.1 port=5003 sync=false async=false \
               udpsrc port=5007 ! rtpbin.recv_rtcp_sink_1
```



### AMR Sink

```
gst-launch-1.0 -v rtpbin name=rtpbin \
                  udpsrc caps="application/x-rtp,media=(string)audio,clock-rate=(int)8000,encoding-name=(string)AMR,encoding-params=(string)1,octet-align=(string)1" port=5002 ! rtpbin.recv_rtp_sink_0 \
                  rtpbin. ! rtpamrdepay ! amrnbdec ! pulsesink udpsrc port=5003 ! rtpbin.recv_rtcp_sink_0 \
                  rtpbin.send_rtcp_src_0 ! udpsink  port=5007 sync=false async=false host=127.0.0.1
```

#### with SRTP Source
```
gst-launch-1.0 rtpbin name=rtpbin \
               audiotestsrc ! amrnbenc ! rtpamrpay ! 'application/x-rtp, payload=(int)96, ssrc=(uint)1356955624' ! rtpbin.send_rtp_sink_1 \
               rtpbin.send_rtp_src_1 ! srtpenc key="012345678901234567890123456789012345678901234567890123456789" ! udpsink host=127.0.0.1 port=5002 \
               rtpbin.send_rtcp_src_1 ! srtpenc key="012345678901234567890123456789012345678901234567890123456789" ! udpsink host=127.0.0.1 port=5003 sync=false async=false  \
               udpsrc port=5007 ! rtpbin.recv_rtcp_sink_1

```

#### with SRTP sink
```
gst-launch-1.0 -v rtpbin name=rtpbin \
                  udpsrc caps='application/x-srtp,media=(string)audio,clock-rate=(int)8000,encoding-name=(string)AMR,encoding-params=(string)1,octet-align=(string)1, ssrc=(uint)1356955624, srtp-key=(buffer)012345678901234567890123456789012345678901234567890123456789, srtp-cipher=(string)aes-128-icm, srtp-auth=(string)hmac-sha1-80, srtcp-cipher=(string)aes-128-icm, srtcp-auth=(string)hmac-sha1-80'  port=5002 ! srtpdec name=dec_rtp ! rtpbin.recv_rtp_sink_0 \
                  udpsrc port=5003 caps='application/x-srtp, srtp-key=(buffer)012345678901234567890123456789012345678901234567890123456789, srtp-cipher=(string)aes-128-icm, srtp-auth=(string)hmac-sha1-80, srtcp-cipher=(string)aes-128-icm, srtcp-auth=(string)hmac-sha1-80' ! srtpdec name=dec_srtp ! rtpbin.recv_rtcp_sink_0 \
                  rtpbin. ! rtpamrdepay ! amrnbdec ! pulsesink \
                  rtpbin.send_rtcp_src_0 ! udpsink  port=5007 sync=false async=false host=127.0.0.1
```

# GES

ges-launch-1.0 +clip ~/Documents/Medias/background.mp4 duration=3.0 -o ~/Documents/Medias/background.mp4
