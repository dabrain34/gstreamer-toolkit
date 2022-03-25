PEER_V=5004 PEER_VSSRC=112233 PEER_IP=127.0.0.1 \
PEER_KEY="4142434445464748494A4B4C4D4E4F505152535455565758595A31323334" \
SELF_V=9004 SELF_VSSRC=332211 \
SELF_SRTP_AUDIO_KEY="012345678901234567890123456789012345678901234567890123456789" \
SELF_SRTP_RTCP_KEY="012345678901234567890123456789012345678901234567890123456789" \
SRTP_AUDIO_CAPS="application/x-srtp,media=(string)audio,clock-rate=(int)8000,\
		   encoding-name=(string)AMR,encoding-params=(string)1,octet-align=(string)1,\
		   ssrc=(uint)1356955624, srtp-key=(buffer)$SELF_SRTP_AUDIO_KEY,\
		   srtp-cipher=(string)aes-128-icm, srtp-auth=(string)hmac-sha1-80, srtcp-cipher=(string)aes-128-icm,\
		   srtcp-auth=(string)hmac-sha1-80"
SRTP_RTCP_CAPS="application/x-srtp,\
		   ssrc=(uint)1356955624, srtp-key=(buffer)$SELF_SRTP_RTCP_KEY,\
		   srtp-cipher=(string)aes-128-icm, srtp-auth=(string)hmac-sha1-80, srtcp-cipher=(string)aes-128-icm,\
		   srtcp-auth=(string)hmac-sha1-80"

set -x
gst-launch-1.0 -v rtpbin name=rtpbin \
                  udpsrc port=5002 ! $SRTP_AUDIO_CAPS ! srtpdec name=dec_rtp ! rtpbin.recv_rtp_sink_0 \
                  udpsrc port=5003 ! $SRTP_RTCP_CAPS ! srtpdec name=dec_rtcp ! rtpbin.recv_rtcp_sink_0 \
                  rtpbin. ! rtpamrdepay ! amrnbdec ! autoaudiosink \
                  rtpbin.send_rtcp_src_0 ! udpsink  port=5007 sync=false async=false host=$PEER_IP
