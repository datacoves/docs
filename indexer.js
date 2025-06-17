const { readdir, readFile, writeFile } = require('fs').promises;
const { relative, resolve } = require('path');
const { argv, exit } = require('process');
const MiniSearch = require('minisearch');

/*
 * Recursively fetch all files from a given directory
 */
async function* getHtmlFiles(dir) {
  const dirents = await readdir(dir, { withFileTypes: true });
  for (const dirent of dirents) {
    const res = resolve(dir, dirent.name);

    if (dirent.isDirectory()) {
      yield* getHtmlFiles(res);
    } else if (dirent.name.endsWith('.html')) {
      yield res;
    }
  }
}

if (argv.length != 4) {
    // error
    console.log("Required parameters: directory to index, and index file");
    exit(1);
}

const input_path = argv[2];
const index_file = argv[3];

const documents = [];

;(async () => {
  for await (const filename of getHtmlFiles(input_path)) {
    const content = (await readFile(filename)).toString();  
    const slice_content = content.split('<article class="markdown-section" id="main">');
    if (slice_content.length < 2) {
      continue;
    }
    const slice_again = slice_content[1].split('</article>');
    const body = slice_again[0].replace(/<[^>]*>?/gm, '').trim();
  
    let url = "/" + relative(input_path, filename);
  
    if (url.endsWith('index.html')) {
        url = url.substr(0, url.length - 10);
    }
  
    documents.push({
        id: relative(input_path, filename),
        text: body,
        url: url,
        snip: body,
    });
  }

  const miniSearch = new MiniSearch({
    fields: ['text'],
    storeFields: ['url', 'snip'],
  });

  await miniSearch.addAllAsync(documents);
  await writeFile(index_file, JSON.stringify(miniSearch.toJSON()));
})();
