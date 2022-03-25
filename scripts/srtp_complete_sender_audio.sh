PEER_V=9004 PEER_VSSRC=332211 PEER_IP=127.0.0.1 \
PEER_KEY="343332315A595857565554535251504F4E4D4C4B4A494847464544434241" \
SELF_V=5004 SELF_VSSRC=112233 \
SELF_KEY="012345678901234567890123456789012345678901234567890123456789" \
RTP_CAPS="application/x-rtp, payload=(int)96, ssrc=(uint)1356955624"

set -x
gst-launch-1.0 -v rtpbin name=rtpbin \
               audiotestsrc ! amrnbenc ! rtpamrpay ! $RTP_CAPS ! rtpbin.send_rtp_sink_1 \
               rtpbin.send_rtp_src_1 ! srtpenc key="$SELF_KEY" ! udpsink host=$PEER_IP port=5002 \
               rtpbin.send_rtcp_src_1 ! srtpenc key="$SELF_KEY" ! udpsink host=$PEER_IP port=5003 sync=false async=false  \
               udpsrc port=5007 ! rtpbin.recv_rtcp_sink_1


