const http = require('http');
const args = process.argv.slice(2);
let port = process.env.PORT || 8080;
const i = args.indexOf('--port');
if (i >= 0 && args[i + 1]) port = parseInt(args[i + 1], 10);
http.createServer((_, r) => r.end('Python bot project — see advanced_quiz_bot.py')).listen(port, () => {
  console.log('stub server listening on', port);
});
