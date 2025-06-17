# Datacoves Docs

## Welcome to the Datacoves Documentation

Our Mission is to be the _fast track to the Modern Data Stack_ so you can focus on **Delivering Results Quickly.**

## Contributing

We use [docsify](https://docsify.js.org/) to generate our documentation.

It's simple, you just need to [learn Markdown](https://jhildenbiddle.github.io/docsify-themeable/#/markdown).

### Install docsify

It is recommended to install docsify-cli globally, which helps initializing and previewing the website locally.

```shell
npm i docsify-cli -g
```

### Preview it

```shell
docsify serve docs
```

### Add new links to the sidebar

Open [docs/\_sidebar.md](docs/_sidebar.md) and add the new links accordingly.

## Static HTML Builder

Because Docsify isn't search engine friendly, and because they don't currently support a server side rendering feature, we have made our own 'compiler' to convert the documentation into static HTML.

To use it, set up a Python virtual environment such as:

```
python3 -m venv venv
```

Then activate it:

```
source venv/bin/activate
```

Install dependencies:

```
pip3 install -r requirements.txt
```

Then run the compiler.  We recommend using the directory named 'output' for the results:

```
python3 -m doc_compiler docs output
```

Note that the resulting files, if just opened from the file system with a web browser, won't handle their paths correctly.  Thus, you have to use some kind of web server to service this.  Any webserver that can serve static content can do this.  For example, if you have PHP installed, you can use its baked in server like this:

```
cd output
php -S 0.0.0.0:8888
```

Then it becomes available on http://localhost:8888

Of course, any web server will work -- you can install NGINX and put the output files in your webroot for instance.


### Warning: Spacing Fussiness

Python's markdown library is fussier than Docsify's when it comes to spacing.  Generally, if your markdown isn't converting correctly, it's one of two problems; either you need a blank line before the line that is breaking, or you need to make sure your indentation is exactly 2 spaces.

For instance, this:

```
## Header text
- Some List
- Like this
- More elements
```

Will render the list items inline with the header text.  You need a blank line above the list:

```
## Header text

- Some List
- Like this
- More elements
```

Or, the other example, spacing.  This will render correctly in Docsify, but will show up as a block-quote in the compiled HTML version:

```
  - This
  - List
  - Doesn't
  - Need
  - Spaces
```

It should simply be:

```
- This
- List
- Doesn't
- Need
- Spaces
```

You can get odd results if you nest lists incorrectly, like:

```
- This is a
- List
   - This one is nested
   - But it has 3 spaces instead of 4, so it will
   - show up in docsify but not python
```

This should be like this instead:

```
- This is a
- List
  - This one is nested
  - But it has 3 spaces instead of 4, so it will
  - show up in docsify but not python
```

... with just 2 spaces before the nested list items.  It is almost always one of these problems if you have a rendering issue, so check your spaces and make sure you have blank lines before new block elements.

### Tabs Functionality

Please see the [docsify-tabs](https://jhildenbiddle.github.io/docsify-tabs/#/) 
