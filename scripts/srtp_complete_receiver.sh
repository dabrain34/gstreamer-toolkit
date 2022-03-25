PEER_V=5004 PEER_VSSRC=112233 PEER_IP=127.0.0.1 \
PEER_KEY="4142434445464748494A4B4C4D4E4F505152535455565758595A31323334" \
SELF_V=9004 SELF_VSSRC=332211 \
SELF_KEY="343332315A595857565554535251504F4E4D4C4B4A494847464544434241" \
SRTP_CAPS="payload=(int)103,ssrc=(uint)$PEER_VSSRC,roc=(uint)0, \
    srtp-key=(buffer)$PEER_KEY, \
    srtp-cipher=(string)aes-128-icm,srtp-auth=(string)hmac-sha1-80, \
    srtcp-cipher=(string)aes-128-icm,srtcp-auth=(string)hmac-sha1-80" \
CAPS_V="media=(string)video,clock-rate=(int)90000,encoding-name=(string)H264,payload=(int)103"
set -x
gst-launch-1.0 -e \
    rtpsession name=r sdes="application/x-rtp-source-sdes,cname=(string)\"recv\@example.com\"" \
    srtpenc name=e key="$SELF_KEY" \
        rtp-cipher="aes-128-icm" rtp-auth="hmac-sha1-80" \
        rtcp-cipher="aes-128-icm" rtcp-auth="hmac-sha1-80" \
    srtpdec name=d \
    udpsrc port=$SELF_V \
        ! "application/x-srtp,$SRTP_CAPS" \
        ! d.rtp_sink \
    d.rtp_src \
        ! "application/x-rtp,$CAPS_V" \
        ! r.recv_rtp_sink \
    r.recv_rtp_src \
        ! rtph264depay \
        ! decodebin \
        ! autovideosink \
    udpsrc port=$((SELF_V+1)) \
        ! "application/x-srtcp,$SRTP_CAPS" \
        ! d.rtcp_sink \
    d.rtcp_src \
        ! r.recv_rtcp_sink \
    fakesrc num-buffers=-1 sizetype=2 \
        ! "application/x-rtp,payload=(int)103,ssrc=(uint)$SELF_VSSRC" \
        ! r.send_rtp_sink \
    r.send_rtp_src \
        ! fakesink async=false \
    r.send_rtcp_src \
        ! e.rtcp_sink_0 \
    e.rtcp_src_0 \
        ! udpsink host=$PEER_IP port=$((PEER_V+1)) sync=false async=false
