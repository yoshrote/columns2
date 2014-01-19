# -*- coding: UTF-8 -*-
import unittest

class TestStripHTML(unittest.TestCase):
    def setUp(self):
        self.content = u"""This is a <div>
            <script type="text/javascript">var a=14;</script>
            <a href="">test link</a>.
            <script src=""/>
            <p>dolor ipsum</p>"""
        self.response = u'This is a test link.dolor ipsum'
    
    def test_basic(self):
        # make sure the shuffled sequence does not lose any elements
        from ...lib.html import striphtml
        response = striphtml(self.content)
        self.assertEqual(response, self.response)
    
    def test_blank(self):
        # make sure the shuffled sequence does not lose any elements
        from ...lib.html import striphtml
        response = striphtml(13)
        self.assertEqual(response, u'')
    

class TestStripObjects(unittest.TestCase):
    def setUp(self):
        self.with_object = u"""<p><img src="/media/uploaded/2010/1/ps3-wvi-mod1.jpg" alt="ps3-wvi-mod" title="ps3-wvi-mod" width="565" height="440" class="aligncenter size-full wp-image-570"/>\n\nSo it may not be the actual PS3 on the road but its a good start. This not so little device is basicly a controler with a 5 inch LED screen on it. Whats so special about it is that lets say you need to take a bathroom break or your in the mood to sit outside. There is no need to stop playing your game!</p><p>This device wirelessly recieves video from your PS3 and acts as a monitor and controller for you as you go wherever youd like with in its range of course. Now can you imagine if they implemented this same concept but via Wi-Fi??? I get goosebumps just thinking about it. Heres a video of the device in action. \n\n<object width="425" height="344"><param name="movie" value="http://www.youtube.com/v/MHA7EqaVbk4&amp;color1=0xb1b1b1&amp;color2=0xcfcfcf&amp;hl=en_US&amp;feature=player_embedded&amp;fs=1"></param><param name="allowFullScreen" value="true"></param><param name="allowScriptAccess" value="always"></param><embed src="http://www.youtube.com/v/MHA7EqaVbk4&amp;color1=0xb1b1b1&amp;color2=0xcfcfcf&amp;hl=en_US&amp;feature=player_embedded&amp;fs=1" type="application/x-shockwave-flash" allowfullscreen="true" allowscriptaccess="always" width="425" height="344"></embed></object></p>"""
        self.no_object = u"""<p><img src="/media/uploaded/2010/1/ps3-wvi-mod1.jpg" alt="ps3-wvi-mod" title="ps3-wvi-mod" width="565" height="440" class="aligncenter size-full wp-image-570"/>\n\nSo it may not be the actual PS3 on the road but its a good start. This not so little device is basicly a controler with a 5 inch LED screen on it. Whats so special about it is that lets say you need to take a bathroom break or your in the mood to sit outside. There is no need to stop playing your game!</p><p>This device wirelessly recieves video from your PS3 and acts as a monitor and controller for you as you go wherever youd like with in its range of course. Now can you imagine if they implemented this same concept but via Wi-Fi??? I get goosebumps just thinking about it. Heres a video of the device in action. \n\n</p>"""
        self.with_satay = u"""<p><img src="/media/uploaded/2010/1/ps3-wvi-mod1.jpg" alt="ps3-wvi-mod" title="ps3-wvi-mod" width="565" height="440" class="aligncenter size-full wp-image-570"/>\n\nSo it may not be the actual PS3 on the road but its a good start. This not so little device is basicly a controler with a 5 inch LED screen on it. Whats so special about it is that lets say you need to take a bathroom break or your in the mood to sit outside. There is no need to stop playing your game!</p>\n<p>This device wirelessly recieves video from your PS3 and acts as a monitor and controller for you as you go wherever youd like with in its range of course. Now can you imagine if they implemented this same concept but via Wi-Fi??? I get goosebumps just thinking about it. Heres a video of the device in action. \n\n<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" width="425" id="validFlash1" height="344"><param name="allowScriptAccess" value="always" /><param name="allowFullScreen" value="true" /><param name="movie" value="http://www.youtube.com/v/MHA7EqaVbk4&amp;color1=0xb1b1b1&amp;color2=0xcfcfcf&amp;hl=en_US&amp;feature=player_embedded&amp;fs=1" /><!--[if !IE]>--><object type="application/x-shockwave-flash" data="http://www.youtube.com/v/MHA7EqaVbk4&amp;color1=0xb1b1b1&amp;color2=0xcfcfcf&amp;hl=en_US&amp;feature=player_embedded&amp;fs=1" width="425" height="344"><!--<![endif]--><a href="http://www.adobe.com/go/getflashplayer"><img src="http://www.adobe.com/images/shared/download_buttons/get_flash_player.gif" alt="Get Adobe Flash player" /></a><!--[if !IE]>--></object><!--<![endif]--></object></p>"""
        self.no_satay = u"""<p><img src="/media/uploaded/2010/1/ps3-wvi-mod1.jpg" alt="ps3-wvi-mod" title="ps3-wvi-mod" width="565" height="440" class="aligncenter size-full wp-image-570"/>\n\nSo it may not be the actual PS3 on the road but its a good start. This not so little device is basicly a controler with a 5 inch LED screen on it. Whats so special about it is that lets say you need to take a bathroom break or your in the mood to sit outside. There is no need to stop playing your game!</p>\n<p>This device wirelessly recieves video from your PS3 and acts as a monitor and controller for you as you go wherever youd like with in its range of course. Now can you imagine if they implemented this same concept but via Wi-Fi??? I get goosebumps just thinking about it. Heres a video of the device in action. \n\n</p>"""
        self.with_hr = u"""<p><img src="/media/uploaded/2010/1/ps3-wvi-mod1.jpg" alt="ps3-wvi-mod" title="ps3-wvi-mod" width="565" height="440" class="aligncenter size-full wp-image-570"/>\n\nSo it may not be the actual PS3 on the road but its a good start. This not so little device is basicly a controler with a 5 inch LED screen on it. Whats so special about it is that lets say you need to take a bathroom break or your in the mood to sit outside. There is no need to stop playing your game!</p><hr/> <p>This device wirelessly recieves video from your PS3 and acts as a monitor and controller for you as you go wherever youd like with in its range of course. Now can you imagine if they implemented this same concept but via Wi-Fi??? I get goosebumps just thinking about it. Heres a video of the device in action. \n\n"""
        self.no_hr = u"""<p><img src="/media/uploaded/2010/1/ps3-wvi-mod1.jpg" alt="ps3-wvi-mod" title="ps3-wvi-mod" width="565" height="440" class="aligncenter size-full wp-image-570"/>\n\nSo it may not be the actual PS3 on the road but its a good start. This not so little device is basicly a controler with a 5 inch LED screen on it. Whats so special about it is that lets say you need to take a bathroom break or your in the mood to sit outside. There is no need to stop playing your game!</p>"""
    
    def test_removeembededobject(self):
        # make sure the shuffled sequence does not lose any elements
        from ...lib.html import stripobjects
        response = stripobjects(self.with_object)
        self.assertEqual(response, self.no_object)
    
    def test_remove_embed(self):
        from ...lib.html import stripobjects
        response = stripobjects("""<div><embed src="http://www.youtube.com/v/JW5meKfy3fY?version=3" type="application/x-shockwave-flash" allowfullscreen="true" allowScriptAccess="always" width="640" height="390"></div>""")
        self.assertEquals(response, """<div/>""")
    
    def test_remove_iframe(self):
        from ...lib.html import stripobjects
        response = stripobjects("""<div><iframe class="youtube-player" type="text/html" width="640" height="385" src="http://www.youtube.com/embed/VIDEO_ID" frameborder="0"></iframe></div>""")
        self.assertEquals(response, """<div/>""")
    
    def test_removesatay(self):
        # make sure the shuffled sequence does not lose any elements
        from ...lib.html import stripobjects
        response = stripobjects(self.with_satay)
        self.assertEqual(response, self.no_satay)
    
    def test_hr(self):
        # make sure the shuffled sequence does not lose any elements
        from ...lib.html import stripobjects
        response = stripobjects(self.with_hr)
        self.assertEqual(response, self.no_hr)
    
    def test_blank(self):
        # make sure the shuffled sequence does not lose any elements
        from ...lib.html import stripobjects
        response = stripobjects(13)
        self.assertEqual(response, u'')
    

class TestGetMetamediaData(unittest.TestCase):
    def test_blank(self):
        from ...lib.html import get_metamedia_data
        res = get_metamedia_data(123)
        self.assertEquals(len(res), 2)
        self.assertEquals(len(res['meta']), 0)
        self.assertEquals(len(res['link']), 0)
    
    def test_img(self):
        from ...lib.html import get_metamedia_data
        res = get_metamedia_data("""<div><img src="http://example.com/img.jpg"/></div>""")
        self.assertEquals(len(res), 2)
        self.assertEquals(len(res['meta']), 0)
        self.assertEquals(len(res['link']), 1)
        self.assertEquals(res['link'].get('image_src'), "http://example.com/img.jpg")
    
    def test_object_w_embed(self):
        from ...lib.html import get_metamedia_data
        res = get_metamedia_data("""<div><<object width="425" height="344"><param name="movie" value="http://www.youtube.com/v/MHA7EqaVbk4&amp;color1=0xb1b1b1&amp;color2=0xcfcfcf&amp;hl=en_US&amp;feature=player_embedded&amp;fs=1"></param><param name="allowFullScreen" value="true"></param><param name="allowScriptAccess" value="always"></param><embed src="http://www.youtube.com/v/MHA7EqaVbk4&amp;color1=0xb1b1b1&amp;color2=0xcfcfcf&amp;hl=en_US&amp;feature=player_embedded&amp;fs=1" type="application/x-shockwave-flash" allowfullscreen="true" allowscriptaccess="always" width="425" height="344"></embed></object></div>""")
        self.assertEquals(len(res), 2)
        self.assertEquals(len(res['meta']), 3)
        self.assertEquals(len(res['link']), 2)
        self.assertEquals(res['meta'].get('video_height'), "344")
        self.assertEquals(res['meta'].get('video_width'), "425")
        self.assertEquals(res['meta'].get('video_type'), "application/x-shockwave-flash")
        self.assertEquals(res['link'].get('video_src'), "http://www.youtube.com/v/MHA7EqaVbk4&color1=0xb1b1b1&color2=0xcfcfcf&hl=en_US&feature=player_embedded&fs=1")
        self.assertEquals(res['link'].get('image_src'), "http://img.youtube.com/vi/MHA7EqaVbk4/default.jpg")
    
    def test_embed(self):
        from ...lib.html import get_metamedia_data
        res = get_metamedia_data("""<div><embed src="http://www.youtube.com/v/JW5meKfy3fY?version=3" type="application/x-shockwave-flash" allowfullscreen="true" allowScriptAccess="always" width="640" height="390"></div>""")
        self.assertEquals(len(res), 2)
        self.assertEquals(len(res['meta']), 3)
        self.assertEquals(len(res['link']), 2)
        self.assertEquals(res['meta'].get('video_height'), "390")
        self.assertEquals(res['meta'].get('video_width'), "640")
        self.assertEquals(res['meta'].get('video_type'), "application/x-shockwave-flash")
        self.assertEquals(res['link'].get('video_src'), "http://www.youtube.com/v/JW5meKfy3fY?version=3")
        self.assertEquals(res['link'].get('image_src'), "http://img.youtube.com/vi/JW5meKfy3fY/default.jpg")
    
    def test_object_w_flashvar(self):
        from ...lib.html import get_metamedia_data
        res = get_metamedia_data("""<div><object type="application/x-shockwave-flash" data="http://i.dmdentertainment.com/DMVideoPlayer/player_test.swf" id="player" height="365" width="650" ><param name="allowScriptAccess" value="always" /><param name="allowFullScreen" value="true" /><param name="movie" value="http://i.dmdentertainment.com/DMVideoPlayer/player_test.swf" /><param name="flashVars" value="demand_rvdisplaymode=2&demand_iconlink=http%3A//www.cracked.com/&demand_rvthumb=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fimage%2F4%2F2%2F2%2F61422.jpg%3Fv%3D1&DESC=&demand_bghex=0&height=22&KEYWORDS=&TITLE=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_rvbg=&adPartner=Adap&demand_continuous_play=1&demand_page_url=http%3A%2F%2Fwww.cracked.com%2Fvideo_18280_friendly-fire-marshal.html&demand_uihex=FFD000&demand_content_id=18280&COMPANION_DIV_ID=adaptv_ad_companion_div&demand_site_id=CRCC&demand_rvpip=0&sitename=Cracked.com&comscore_c3=7290858&demand_cat=Movies+%26+TV&demand_autoplay=0&ADPTAG=GoodNeighbor&video_title=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_content_sourcekey=cracked.com&KEY=DemandMediacracked&skin=http%3A//i.dmdentertainment.com/DMVideoPlayer/playerskin_test.swf&demand_show_replay=true&ADAPTAG=&CATEGORIES=Movies+%26+TV&source=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&URL=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&demand_preroll=false&demand_iconurl=http%3A//i-beta.crackedcdn.com/ui/shared/images/global/icons/Video_Cracked.png&ID=18252&demand_related=1&demand_preroll_source=http%3A//i-beta.crackedcdn.com/ui/shared/resources/Pre-Roll1b_cr.swf&demand_icontext=Watch%20more%20videos%20at%20Cracked.com%20America%27s%20only%20humor%20site.&v=3.0.6.f&wa_vemb=1" /></object></div>""", 'http://media.nerdblerp.com/media/409294_300.jpg')
        self.assertEquals(len(res), 2)
        self.assertEquals(len(res['meta']), 3)
        self.assertEquals(len(res['link']), 2)
        self.assertEquals(res['meta'].get('video_height'), "365")
        self.assertEquals(res['meta'].get('video_width'), "650")
        self.assertEquals(res['meta'].get('video_type'), "application/x-shockwave-flash")
        self.assertEquals(res['link'].get('video_src'), "http://i.dmdentertainment.com/DMVideoPlayer/player_test.swf?demand_rvdisplaymode=2&demand_iconlink=http%3A//www.cracked.com/&demand_rvthumb=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fimage%2F4%2F2%2F2%2F61422.jpg%3Fv%3D1&DESC=&demand_bghex=0&height=22&KEYWORDS=&TITLE=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_rvbg=&adPartner=Adap&demand_continuous_play=1&demand_page_url=http%3A%2F%2Fwww.cracked.com%2Fvideo_18280_friendly-fire-marshal.html&demand_uihex=FFD000&demand_content_id=18280&COMPANION_DIV_ID=adaptv_ad_companion_div&demand_site_id=CRCC&demand_rvpip=0&sitename=Cracked.com&comscore_c3=7290858&demand_cat=Movies+%26+TV&demand_autoplay=0&ADPTAG=GoodNeighbor&video_title=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_content_sourcekey=cracked.com&KEY=DemandMediacracked&skin=http%3A//i.dmdentertainment.com/DMVideoPlayer/playerskin_test.swf&demand_show_replay=true&ADAPTAG=&CATEGORIES=Movies+%26+TV&source=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&URL=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&demand_preroll=false&demand_iconurl=http%3A//i-beta.crackedcdn.com/ui/shared/images/global/icons/Video_Cracked.png&ID=18252&demand_related=1&demand_preroll_source=http%3A//i-beta.crackedcdn.com/ui/shared/resources/Pre-Roll1b_cr.swf&demand_icontext=Watch%20more%20videos%20at%20Cracked.com%20America%27s%20only%20humor%20site.&v=3.0.6.f&wa_vemb=1")
        self.assertEquals(res['link'].get('image_src'), "http://media.nerdblerp.com/media/409294_300.jpg")
    
    def test_object_w_flashvar2(self):
        from ...lib.html import get_metamedia_data
        res = get_metamedia_data("""<div><object type="application/x-shockwave-flash" data="http://i.dmdentertainment.com/DMVideoPlayer/player_test.swf" id="player" height="365" width="650" ><param name="type" value="application/x-shockwave-flash"/> <param name="allowScriptAccess" value="always" /><param name="allowFullScreen" value="true" /><param name="src" value="http://i.dmdentertainment.com/DMVideoPlayer/player_test.swf" /><param name="flashVars" value="demand_rvdisplaymode=2&demand_iconlink=http%3A//www.cracked.com/&demand_rvthumb=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fimage%2F4%2F2%2F2%2F61422.jpg%3Fv%3D1&DESC=&demand_bghex=0&height=22&KEYWORDS=&TITLE=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_rvbg=&adPartner=Adap&demand_continuous_play=1&demand_page_url=http%3A%2F%2Fwww.cracked.com%2Fvideo_18280_friendly-fire-marshal.html&demand_uihex=FFD000&demand_content_id=18280&COMPANION_DIV_ID=adaptv_ad_companion_div&demand_site_id=CRCC&demand_rvpip=0&sitename=Cracked.com&comscore_c3=7290858&demand_cat=Movies+%26+TV&demand_autoplay=0&ADPTAG=GoodNeighbor&video_title=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_content_sourcekey=cracked.com&KEY=DemandMediacracked&skin=http%3A//i.dmdentertainment.com/DMVideoPlayer/playerskin_test.swf&demand_show_replay=true&ADAPTAG=&CATEGORIES=Movies+%26+TV&source=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&URL=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&demand_preroll=false&demand_iconurl=http%3A//i-beta.crackedcdn.com/ui/shared/images/global/icons/Video_Cracked.png&ID=18252&demand_related=1&demand_preroll_source=http%3A//i-beta.crackedcdn.com/ui/shared/resources/Pre-Roll1b_cr.swf&demand_icontext=Watch%20more%20videos%20at%20Cracked.com%20America%27s%20only%20humor%20site.&v=3.0.6.f&wa_vemb=1" /></object></div>""", 'http://media.nerdblerp.com/media/409294_300.jpg')
        self.assertEquals(len(res), 2)
        self.assertEquals(len(res['meta']), 3)
        self.assertEquals(len(res['link']), 2)
        self.assertEquals(res['meta'].get('video_height'), "365")
        self.assertEquals(res['meta'].get('video_width'), "650")
        self.assertEquals(res['meta'].get('video_type'), "application/x-shockwave-flash")
        self.assertEquals(res['link'].get('video_src'), "http://i.dmdentertainment.com/DMVideoPlayer/player_test.swf?demand_rvdisplaymode=2&demand_iconlink=http%3A//www.cracked.com/&demand_rvthumb=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fimage%2F4%2F2%2F2%2F61422.jpg%3Fv%3D1&DESC=&demand_bghex=0&height=22&KEYWORDS=&TITLE=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_rvbg=&adPartner=Adap&demand_continuous_play=1&demand_page_url=http%3A%2F%2Fwww.cracked.com%2Fvideo_18280_friendly-fire-marshal.html&demand_uihex=FFD000&demand_content_id=18280&COMPANION_DIV_ID=adaptv_ad_companion_div&demand_site_id=CRCC&demand_rvpip=0&sitename=Cracked.com&comscore_c3=7290858&demand_cat=Movies+%26+TV&demand_autoplay=0&ADPTAG=GoodNeighbor&video_title=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_content_sourcekey=cracked.com&KEY=DemandMediacracked&skin=http%3A//i.dmdentertainment.com/DMVideoPlayer/playerskin_test.swf&demand_show_replay=true&ADAPTAG=&CATEGORIES=Movies+%26+TV&source=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&URL=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&demand_preroll=false&demand_iconurl=http%3A//i-beta.crackedcdn.com/ui/shared/images/global/icons/Video_Cracked.png&ID=18252&demand_related=1&demand_preroll_source=http%3A//i-beta.crackedcdn.com/ui/shared/resources/Pre-Roll1b_cr.swf&demand_icontext=Watch%20more%20videos%20at%20Cracked.com%20America%27s%20only%20humor%20site.&v=3.0.6.f&wa_vemb=1")
        self.assertEquals(res['link'].get('image_src'), "http://media.nerdblerp.com/media/409294_300.jpg")
    
    def test_object_w_flashvar3(self):
        from ...lib.html import get_metamedia_data
        res = get_metamedia_data("""<div><object type="application/x-shockwave-flash" data="http://i.dmdentertainment.com/DMVideoPlayer/player_test.swf" id="player" height="365" width="650" ><param name="type" value="application/x-shockwave-flash"/> <param name="allowScriptAccess" value="always" /><param name="allowFullScreen" value="true" /><param name="src" value="http://i.dmdentertainment.com/DMVideoPlayer/player_test.swf" /><param name="flashVars" value="&demand_rvdisplaymode=2&demand_iconlink=http%3A//www.cracked.com/&demand_rvthumb=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fimage%2F4%2F2%2F2%2F61422.jpg%3Fv%3D1&DESC=&demand_bghex=0&height=22&KEYWORDS=&TITLE=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_rvbg=&adPartner=Adap&demand_continuous_play=1&demand_page_url=http%3A%2F%2Fwww.cracked.com%2Fvideo_18280_friendly-fire-marshal.html&demand_uihex=FFD000&demand_content_id=18280&COMPANION_DIV_ID=adaptv_ad_companion_div&demand_site_id=CRCC&demand_rvpip=0&sitename=Cracked.com&comscore_c3=7290858&demand_cat=Movies+%26+TV&demand_autoplay=0&ADPTAG=GoodNeighbor&video_title=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_content_sourcekey=cracked.com&KEY=DemandMediacracked&skin=http%3A//i.dmdentertainment.com/DMVideoPlayer/playerskin_test.swf&demand_show_replay=true&ADAPTAG=&CATEGORIES=Movies+%26+TV&source=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&URL=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&demand_preroll=false&demand_iconurl=http%3A//i-beta.crackedcdn.com/ui/shared/images/global/icons/Video_Cracked.png&ID=18252&demand_related=1&demand_preroll_source=http%3A//i-beta.crackedcdn.com/ui/shared/resources/Pre-Roll1b_cr.swf&demand_icontext=Watch%20more%20videos%20at%20Cracked.com%20America%27s%20only%20humor%20site.&v=3.0.6.f&wa_vemb=1" /></object></div>""", 'http://media.nerdblerp.com/media/409294_300.jpg')
        self.assertEquals(len(res), 2)
        self.assertEquals(len(res['meta']), 3)
        self.assertEquals(len(res['link']), 2)
        self.assertEquals(res['meta'].get('video_height'), "365")
        self.assertEquals(res['meta'].get('video_width'), "650")
        self.assertEquals(res['meta'].get('video_type'), "application/x-shockwave-flash")
        self.assertEquals(res['link'].get('video_src'), "http://i.dmdentertainment.com/DMVideoPlayer/player_test.swf?demand_rvdisplaymode=2&demand_iconlink=http%3A//www.cracked.com/&demand_rvthumb=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fimage%2F4%2F2%2F2%2F61422.jpg%3Fv%3D1&DESC=&demand_bghex=0&height=22&KEYWORDS=&TITLE=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_rvbg=&adPartner=Adap&demand_continuous_play=1&demand_page_url=http%3A%2F%2Fwww.cracked.com%2Fvideo_18280_friendly-fire-marshal.html&demand_uihex=FFD000&demand_content_id=18280&COMPANION_DIV_ID=adaptv_ad_companion_div&demand_site_id=CRCC&demand_rvpip=0&sitename=Cracked.com&comscore_c3=7290858&demand_cat=Movies+%26+TV&demand_autoplay=0&ADPTAG=GoodNeighbor&video_title=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_content_sourcekey=cracked.com&KEY=DemandMediacracked&skin=http%3A//i.dmdentertainment.com/DMVideoPlayer/playerskin_test.swf&demand_show_replay=true&ADAPTAG=&CATEGORIES=Movies+%26+TV&source=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&URL=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&demand_preroll=false&demand_iconurl=http%3A//i-beta.crackedcdn.com/ui/shared/images/global/icons/Video_Cracked.png&ID=18252&demand_related=1&demand_preroll_source=http%3A//i-beta.crackedcdn.com/ui/shared/resources/Pre-Roll1b_cr.swf&demand_icontext=Watch%20more%20videos%20at%20Cracked.com%20America%27s%20only%20humor%20site.&v=3.0.6.f&wa_vemb=1")
        self.assertEquals(res['link'].get('image_src'), "http://media.nerdblerp.com/media/409294_300.jpg")
    
    def test_object_w_flashvar4(self):
        from ...lib.html import get_metamedia_data
        res = get_metamedia_data("""<div><object type="application/x-shockwave-flash" data="http://i.dmdentertainment.com/DMVideoPlayer/player_test.swf" id="player" height="365" width="650" ><param name="type" value="application/x-shockwave-flash"/> <param name="allowScriptAccess" value="always" /><param name="allowFullScreen" value="true" /><param name="src" value="http://i.dmdentertainment.com/DMVideoPlayer/player_test.swf?demand_iconlink=http%3A//www.cracked.com/" /><param name="flashVars" value="demand_rvdisplaymode=2&demand_rvthumb=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fimage%2F4%2F2%2F2%2F61422.jpg%3Fv%3D1&DESC=&demand_bghex=0&height=22&KEYWORDS=&TITLE=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_rvbg=&adPartner=Adap&demand_continuous_play=1&demand_page_url=http%3A%2F%2Fwww.cracked.com%2Fvideo_18280_friendly-fire-marshal.html&demand_uihex=FFD000&demand_content_id=18280&COMPANION_DIV_ID=adaptv_ad_companion_div&demand_site_id=CRCC&demand_rvpip=0&sitename=Cracked.com&comscore_c3=7290858&demand_cat=Movies+%26+TV&demand_autoplay=0&ADPTAG=GoodNeighbor&video_title=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_content_sourcekey=cracked.com&KEY=DemandMediacracked&skin=http%3A//i.dmdentertainment.com/DMVideoPlayer/playerskin_test.swf&demand_show_replay=true&ADAPTAG=&CATEGORIES=Movies+%26+TV&source=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&URL=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&demand_preroll=false&demand_iconurl=http%3A//i-beta.crackedcdn.com/ui/shared/images/global/icons/Video_Cracked.png&ID=18252&demand_related=1&demand_preroll_source=http%3A//i-beta.crackedcdn.com/ui/shared/resources/Pre-Roll1b_cr.swf&demand_icontext=Watch%20more%20videos%20at%20Cracked.com%20America%27s%20only%20humor%20site.&v=3.0.6.f&wa_vemb=1" /></object></div>""", 'http://media.nerdblerp.com/media/409294_300.jpg')
        self.assertEquals(len(res), 2)
        self.assertEquals(len(res['meta']), 3)
        self.assertEquals(len(res['link']), 2)
        self.assertEquals(res['meta'].get('video_height'), "365")
        self.assertEquals(res['meta'].get('video_width'), "650")
        self.assertEquals(res['meta'].get('video_type'), "application/x-shockwave-flash")
        self.assertEquals(res['link'].get('video_src'), "http://i.dmdentertainment.com/DMVideoPlayer/player_test.swf?demand_iconlink=http%3A//www.cracked.com/&demand_rvdisplaymode=2&demand_rvthumb=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fimage%2F4%2F2%2F2%2F61422.jpg%3Fv%3D1&DESC=&demand_bghex=0&height=22&KEYWORDS=&TITLE=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_rvbg=&adPartner=Adap&demand_continuous_play=1&demand_page_url=http%3A%2F%2Fwww.cracked.com%2Fvideo_18280_friendly-fire-marshal.html&demand_uihex=FFD000&demand_content_id=18280&COMPANION_DIV_ID=adaptv_ad_companion_div&demand_site_id=CRCC&demand_rvpip=0&sitename=Cracked.com&comscore_c3=7290858&demand_cat=Movies+%26+TV&demand_autoplay=0&ADPTAG=GoodNeighbor&video_title=Agents+of+Cracked%3A+Taking+Office+Politics+Way+Too+Seriously&demand_content_sourcekey=cracked.com&KEY=DemandMediacracked&skin=http%3A//i.dmdentertainment.com/DMVideoPlayer/playerskin_test.swf&demand_show_replay=true&ADAPTAG=&CATEGORIES=Movies+%26+TV&source=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&URL=http%3A%2F%2Fi-beta.crackedcdn.com%2Fphpimages%2Fvideos%2F0%2F8%2F3%2F63083_608X342.flv&demand_preroll=false&demand_iconurl=http%3A//i-beta.crackedcdn.com/ui/shared/images/global/icons/Video_Cracked.png&ID=18252&demand_related=1&demand_preroll_source=http%3A//i-beta.crackedcdn.com/ui/shared/resources/Pre-Roll1b_cr.swf&demand_icontext=Watch%20more%20videos%20at%20Cracked.com%20America%27s%20only%20humor%20site.&v=3.0.6.f&wa_vemb=1")
        self.assertEquals(res['link'].get('image_src'), "http://media.nerdblerp.com/media/409294_300.jpg")
    

class TestGetPostThumbnail(unittest.TestCase):
    def test_vimeo_thumb(self):
        from ...lib.html import get_post_thumbnail
        get_post_thumbnail("http://vimeo.com/moogaloop.swf?clip_id=12337669&amp;server=vimeo.com&amp;show_title=0&amp;show_byline=0&amp;show_portrait=0&amp;color=00adef&amp;fullscreen=1&amp;autoplay=0&amp;loop=0")
    
    def test_youtube_thumb(self):
        from ...lib.html import get_post_thumbnail
        get_post_thumbnail("http://www.youtube.com/embed/Cb3hoZu3hzY")
    
    def test_default_thumb(self):
        from ...lib.html import get_post_thumbnail
        get_post_thumbnail("http://www.notarealsite.com/whocares")
    

