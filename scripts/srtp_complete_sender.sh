PEER_V=9004 PEER_VSSRC=332211 PEER_IP=127.0.0.1 \
PEER_KEY="343332315A595857565554535251504F4E4D4C4B4A494847464544434241" \
SELF_V=5004 SELF_VSSRC=112233 \
SELF_KEY="4142434445464748494A4B4C4D4E4F505152535455565758595A31323334" \
SRTP_CAPS="payload=(int)103,ssrc=(uint)$PEER_VSSRC,roc=(uint)0, \
    srtp-key=(buffer)$PEER_KEY, \
    srtp-cipher=(string)aes-128-icm,srtp-auth=(string)hmac-sha1-80, \
    srtcp-cipher=(string)aes-128-icm,srtcp-auth=(string)hmac-sha1-80" 
set -x 
gst-launch-1.0 -e \
    rtpsession name=r sdes="application/x-rtp-source-sdes,cname=(string)\"user\@example.com\"" \
    srtpenc name=e key="$SELF_KEY" \
        rtp-cipher="aes-128-icm" rtp-auth="hmac-sha1-80" \
        rtcp-cipher="aes-128-icm" rtcp-auth="hmac-sha1-80" \
    srtpdec name=d \
    videotestsrc \
        ! videoconvert ! x264enc tune=zerolatency \
        ! rtph264pay \
        ! "application/x-rtp,payload=(int)103,ssrc=(uint)$SELF_VSSRC" \
        ! r.send_rtp_sink \
    r.send_rtp_src \
        ! e.rtp_sink_0 \
    e.rtp_src_0 \
        ! udpsink host=$PEER_IP port=$PEER_V \
    r.send_rtcp_src \
        ! e.rtcp_sink_0 \
    e.rtcp_src_0 \
        ! udpsink host=$PEER_IP port=$((PEER_V+1)) sync=false async=false \
    udpsrc port=$((SELF_V+1)) \
        ! "application/x-srtcp,$SRTP_CAPS" \
        ! d.rtcp_sink \
    d.rtcp_src \
        ! tee name=t \
        t. ! queue ! r.recv_rtcp_sink \
        t. ! queue ! fakesink dump=true async=false
