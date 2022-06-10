// ==UserScript==
// @name         idarthelper Dev
// @namespace    idarthelper
// @version      0.6.4
// @description  idart 工具, 下载附件, 下载 bug2go, 下载 fastboot 刷机包
// @match        https://idart.mot.com/browse/*
// @match        https://mmibug2go.appspot.com/*
// @run-at       document-idle
// @grant        GM_xmlhttpRequest
// @grant        GM_log
// @grant        GM_addStyle
// @grant        GM_cookie
// @require      https://code.jquery.com/jquery-3.6.0.min.js
// ==/UserScript==
(function () {

    'use strict';
    const web_url = window.location.host
    const artifacts_host = 'https://artifacts-bjmirr.mot.com/artifactory/webapp/#/home'

    function drag_element(element) {
        //set 4 positions for positioning on the screen
        let pos1 = 0,
            pos2 = 0,
            pos3 = 0,
            pos4 = 0;
        element.onpointerdown = pointerDrag;

        function pointerDrag(e) {
            e.preventDefault();
            console.log(e);
            // get the initial mouse cursor position for pos3 and pos4
            pos3 = e.clientX;
            pos4 = e.clientY;
            // when the mouse moves, start the drag
            document.onpointermove = elementDrag;
            // when the mouse is lifted, stop the drag
            document.onpointerup = stopElementDrag;
        }

        function elementDrag(e) {
            // calculate the new cursor position
            // pos1 = where the Xmouse WAS - where it IS
            pos1 = pos3 - e.clientX;
            // pos2 = where the Ymouse WAS - where it IS
            pos2 = pos4 - e.clientY;
            //reset pos3 to current location of Xmouse
            pos3 = e.clientX;
            //reset pos4 to current location of Ymouse
            pos4 = e.clientY;
            console.log(pos1, pos2, pos3, pos4);
            // set the element's new position:
            element.style.top = element.offsetTop - pos2 + 'px';
            element.style.left = element.offsetLeft - pos1 + 'px';
        }

        function stopElementDrag() {
            // stop calculating when mouse is released
            document.onpointerup = null;
            document.onpointermove = null;
        }
    }

    function delay(time) {
        return new Promise(resolve => setTimeout(resolve, time));
    }

    // 添加下载按钮
    function idart() {
        var cookie;
        GM_cookie('list', { url: location.href }, (cookies) => {
            cookie = cookies.map(c => `${c.name}=${c.value}`).join('; ');
        });
        function download_attachment() {
            const attachments = $('.attachment-content')
            if (attachments.length == 0) {
                alert('no attachments')
            } else {

                const id = new RegExp('browse/(.*$)').exec(window.location.href)[1]
                // 获取附件下载地址
                const download_url = 'https://' + window.location.host + $('#aszip').attr('href')
                // 生成json
                const url_json = {
                    "url": download_url,
                    "id": id,
                    // "cookie": document.cookie
                    "cookie": cookie
                }
                // json 转 string
                let url_json_string = JSON.stringify(url_json);
                // 因为json string中有大括号, 无法通过 url 传递, 必须要url编码
                let open_native_python_script_url = "idart://idart//" + encodeURIComponent(url_json_string);
                // 通过url, 打开本地 registry 中注册的python脚本, 下载改附件并解压
                window.open(open_native_python_script_url);
            }
        }
        function download_fastboot() {
            let product=''
            let finger=''
            let version=''
            let dist=''
            let android_version=''
            // 找到的product是类似这样的, Milan (milan)
            // 需要过滤出 () 中的
            const element_product=$('#customfield_18027-val').text()
            if (element_product) {
                const pf = new RegExp('\\((.*)\\)').exec(element_product)
                if (pf.length > 1) {
                    product = pf[1]
                }
            }
            // https://idart.mot.com/browse/IKSWS-119082
            // Build Fingerprint: motorola/eqs_cn/eqs:12/SSQ32.59/e9c75-a5f84:userdebug/intcfg,test-keys
            // 中的 e9c75-a5f84
            const element_build_fingerprint=$('#customfield_14827-val').text()
            if (element_build_fingerprint) {
                const pf = new RegExp('(\\w{5}-\\w{5})').exec(element_build_fingerprint)
                if (pf && pf.length > 1) {
                    finger = pf[1]
                }
                const vera = new RegExp('[\\s/](\\w{1,}\\..*?)[\\s/]').exec(element_build_fingerprint)
                if (vera && vera.length > 1) {
                    version = vera[1]
                }
                const a_vera = new RegExp('[/\\s:](\\d{2})[\\s/]').exec(element_build_fingerprint)
                if (a_vera && a_vera.length > 1) {
                    android_version = a_vera[1]
                }
                const di = new RegExp('[/](\\w{1,}_cn)[/]').exec(element_build_fingerprint)
                if (di && di.length > 1) {
                    dist = di[1]
                }
            }
            // https://idart.mot.com/browse/IKSWS-119082
            // SW Version:eqs_cn-userdebug 12 SSQ32.59 e9c75-a5f84 intcfg,test-keys
            // 找到类似 eqs_cn-userdebug 12 SSQ32.59 e9c75-a5f84 intcfg,test-keys
            const element_sw_version=$('#customfield_10157-val').text()
            if (element_sw_version) {
                const pf = new RegExp('([a-z0-9]{]5}-[a-z0-9]{]5})').exec(element_sw_version)
                // 找到 e9c75-a5f84
                if (pf && pf.length > 1) {
                    finger = pf[1]
                }
                // 中的 SSQ32.59
                const vera = new RegExp('[\\s/](\\w{1,}\\..*?)[\\s/]').exec(element_sw_version)
                if (vera && vera.length > 1) {
                    version = vera[1]
                }
                // 找到 12
                const a_vera = new RegExp('[/\\s:](\\d{2})[\\s/]').exec(element_sw_version)
                if (a_vera && a_vera.length > 1) {
                    android_version = a_vera[1]
                }
            }
            // https://idart.mot.com/browse/IKSWS-118390  OS/SWBuild:oneli_cn-userdebug 12 SSL32.54
            // https://idart.mot.com/browse/IKSWS-42920   OS/SWBuild: rhodep_g_userdebug_12_S1SU32.11_ea7314-ca6cc4_intcfg-test-keys_global_US
            const os_sw_build=$('.user-content-block').text()
            if (os_sw_build) {
                const vera = new RegExp('OS/SWBuild:.*[\\s_](\\w{1,}\\.\\w{1,})[\\s_]').exec(os_sw_build)
                if (vera && vera.length > 1) {
                    version = vera[1]
                }
                const a_vera = new RegExp('OS/SWBuild:.*[\\s_](\\d{2})[\\s_]').exec(os_sw_build)
                if (a_vera && a_vera.length > 1) {
                    android_version = a_vera[1]
                }
                const di = new RegExp('[:/\\-](\\w{1,}_cn)[:/\\-]').exec(element_build_fingerprint)
                if (di && di.length > 1) {
                    dist = di[1]
                }
            }
            const url_json = {
                "url": location.href,
                "product": product,
                "dist": dist,
                "android_version": android_version,
                "version": version,
                "finger": finger
            }

            GM_cookie('list', {
                url: artifacts_host
            }, (cookies) => {
                const cookie = cookies.map(c => `${c.name}=${c.value}`).join('; ');
                const artifacts_json = {
                    'url': "https://artifacts-bjmirr.mot.com/artifactory/ui/treebrowser?compacted=true&$no_spinner=true",
                    'cookie': cookie
                }
                url_json['artifacts'] = artifacts_json
                // json 转 string
                let url_json_string = JSON.stringify(url_json);
                // 因为json string中有大括号, 无法通过 url 传递, 必须要url编码
                let open_native_python_script_url = "idart://artifacts//" + encodeURIComponent(url_json_string);
                // 通过url, 打开本地 registry 中注册的python脚本, 下载改附件并解压
                window.open(open_native_python_script_url);
            });
        }


        $('head').append($(`
        <style>
        .btn-style {
        border: none;
        border-radius: 50%;
        color: #ffffff;
        background: linear-gradient(to right,rgb(255, 71, 166),rgb(210, 161, 8));
        }
        .btn1 {
        height: 80px;
        width: 80px;
        position: absolute;
        bottom: 300px;
        right: 200px;
        }
        .btn2 {
        height: 80px;
        width: 80px;
        position: absolute;
        bottom: 200px;
        right: 200px;
        }
        .btn3 {
        height: 80px;
        width: 80px;
        position: absolute;
        bottom: 100px;
        right: 200px;
        }
        </style>
        `))
        $('.issue-navigator').append($(`
        <div>
        <button class="btn-style btn1" id="down_attachment">Download Attachment</button>
        <button class="btn-style btn2" id="down_bug2go">Download Bug2Go</button>
        <button class="btn-style btn3" id="down_fastboot">Download fastboot</button>
        </div>
        `))

        drag_element(document.getElementById('down_attachment'));
        drag_element(document.getElementById('down_bug2go'));

        $('#down_attachment').on("click", function () {
            download_attachment();
        });

        $('#down_bug2go').on("click", function () {
            const matches = new Set();
            for (const href of document.querySelectorAll('a[href^="https://mmibug2go.appspot.com"]')) {
                matches.add(href.getAttribute('href'))
            }
            for (const href of document.querySelectorAll('a[href][class="external-link"]')) {
                if (href.text.includes("https://mmibug2go.appspot.com"))
                matches.add(href.text)
            }
            if (matches.length != 0) {
                if (matches.length > 1) {
                    alert('More than one bug2go url')
                }
                for (const i of matches) {
                    window.open(i)
                }
            } else {
                alert('No Bug2Go URL');
            }
        });

        $('#down_fastboot').on('click', function() {
            download_fastboot()
        })
    }

    function bug2go() {

        function download(url) {
            const decode_url = decodeURIComponent(url);
            const filename = new RegExp('filename=(.*?)&').exec(decode_url)[1]
            let url_json = {
                "url": url,
                "file_name": filename
            }
            // json 转 string
            const url_json_string = JSON.stringify(url_json)
            // 因为json string中有大括号, 无法通过 url 传递, 必须要url编码
            const open_native_python_script_url = 'idart://bug2go//' + encodeURIComponent(url_json_string)
            // 通过url, 打开本地 registry 中注册的python脚本, 下载改附件并解压
            window.open(open_native_python_script_url)
            // window.close();
        }
        function get_download_url() {
            // 获取标志 id
            const id = new RegExp('[0-9]*$').exec(document.location.href)[0]
            const session_id = new RegExp('JSESSIONID=(.*?); ').exec(document.cookie)[1];

            const getUrl = 'https://mmibug2go.appspot.com/_ah/api/bug2go/v1/bugReports/' +　id + '/downloadUrl?';
            GM_xmlhttpRequest({
                url: getUrl,
                method: "GET",
                headers: {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
                    cookie: document.cookie,
                    "x-bug2go-jsessionid": session_id,
                    Accept: '*/',
                    "Accept-Encoding": 'gzip,deflate,br',
                },
                onload(response) {
                    if (response.status === 200) {
                        GM_log("get download url success");
                        const download_url = JSON.parse(response.responseText).downloadUrl;
                        download(download_url);
                    } else {
                        GM_log("get download url failed: " + response.text);
                    }
                },
            });

        }

        window.onload = function () {
            const loginSign = document.querySelector('div[ng-click="loginCtrl.loginWithLenovo()"]')
            if (loginSign) {
                loginSign.click()
                GM_log("login with Lenovo")
            } else {
                GM_log("aleray login with Lenovo")
                get_download_url()
            }
        }
    }

    if (web_url.indexOf('idart.mot.com') != -1) {
        idart();
    } else if (web_url.indexOf('mmibug2go.appspot.com') != -1) {
        bug2go();
    }
})();