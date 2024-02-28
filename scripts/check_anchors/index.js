const fs = require("fs");
const showdown  = require('showdown');
const jsdom = require("jsdom");

showdown.setFlavor('github');
const converter = new showdown.Converter();

const files = process.argv.slice(2);

for (let path of files) {
    console.log("Checking file", path);
    const text = fs.readFileSync(path, {encoding: "utf-8"});
    const html      = converter.makeHtml(text);
    const dom = new jsdom.JSDOM(html);
    const doc = dom.window.document;
    const links = doc.querySelectorAll("a");
    const errors = [];
    for (var i = 0; i < links.length; i++) {
        var link = links[i].getAttribute("href");
        if (link.startsWith('#')) {
            if (!doc.getElementById(link.slice(1))) {
                console.log('Could not find', link);
                errors.push(link)
            }
        }
    }
    if (errors.length > 0) {
        const all = doc.querySelectorAll('*[id]');
        for (var i = 0; i < all.length; i ++ ) {
            console.log(all[i].id);
        }
        process.exit(1);
    }
}
