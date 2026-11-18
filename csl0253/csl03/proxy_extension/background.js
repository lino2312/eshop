// 代理认证凭据（运行时会被 Python 脚本动态修改）
let PROXY_USER = 'LUuteRCHxpEV';
let PROXY_PASS = '6RCyiJubJJ';

// 监听代理认证请求并自动填写
chrome.webRequest.onAuthRequired.addListener(
  function(details, callbackFn) {
    console.log('Proxy auth required:', details.url);
    
    // 自动提供代理认证凭据
    callbackFn({
      authCredentials: {
        username: PROXY_USER,
        password: PROXY_PASS
      }
    });
  },
  { urls: ['<all_urls>'] },
  ['blocking']
);

console.log('Proxy Auto Auth extension loaded');
console.log('Username:', PROXY_USER);
console.log('Password:', PROXY_PASS);