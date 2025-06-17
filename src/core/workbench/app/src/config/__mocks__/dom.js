import { JSDOM } from 'jsdom';
const dom = new JSDOM();
global.document = dom.window.document;
global.location.hostname = "dev123.datacoveslocal.com";
global.window = dom.window;
