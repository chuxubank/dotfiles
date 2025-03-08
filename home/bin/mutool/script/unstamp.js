function toCharCode(c) {
  return c.charCodeAt(0);
}

function bufSearch(buf, needle, options) {
  options = options || {};
  var start = options.start || 0;
  var end = options.end || buf.length;
  if (typeof needle === "string") {
    needle = Array.prototype.map.call(needle, toCharCode);
  }
  for (var i = start; i < end; i++) {
    for (var j = 0; j < needle.length; j++) {
      if (buf[i + j] !== needle[j]) {
        break;
      }
      if (j === needle.length - 1) {
        return i;
      }
    }
  }
  return null;
}

function deleteObjInDictByNames(objDict, objNames) {
  objNames.forEach(function (x) {
    objDict.delete(x);
  });
}

function findInObjDict(dict, text) {
  var objNames = [];
  dict.forEach(function check(key, value) {
    if (!value || !value.isStream()) {
      return;
    }
    var buffer = value.readStream();
    if (bufSearch(buffer, text)) {
      objNames.push(key);
    }
  });
  return objNames;
}

function processPageObject(obj, text) {
  if (!obj) {
    print("Can not handle ", typeof obj);
    return;
  }
  if (obj.isDictionary()) {
    var objNames = findInObjDict(obj, text);
    deleteObjInDictByNames(obj, objNames);
    return objNames;
  } else {
    print("Not dict", typeof obj, obj.isArray());
  }
}

function removeText(input, text) {
  for (var i = 1; i < input.countPages(); i++) {
    var page = input.findPage(i);
    processPageObject(page.Resources.XObject, text);
  }
}

function removeObject(input, obj) {
  if (!options.silent) {
    print("Deleting object", obj);
  }
  input.deleteObject(obj);
}

function removePage(input, page) {
  if (!options.silent) {
    print("Deleting page", page);
  }
  input.deletePage(page);
}

var options = {
  input: null,
  output: null,
  kill: null,
  remove: null,
  page: null,
  debug: false,
  silent: false,
  help: false,
};

scriptArgs.forEach(function (arg, index) {
  switch (arg) {
    case "-i":
    case "--input":
      options.input = scriptArgs[index + 1];
      break;
    case "-o":
    case "--output":
      options.output = scriptArgs[index + 1];
      break;
    case "-k":
    case "--kill":
      options.kill = scriptArgs[index + 1];
      break;
    case "-r":
    case "--remove":
      options.remove = scriptArgs[index + 1];
      break;
    case "-p":
    case "--page":
      options.page = scriptArgs[index + 1];
      break;
    case "-d":
    case "--debug":
      options.debug = true;
      break;
    case "-s":
    case "--silent":
      options.silent = true;
      break;
    case "-h":
    case "--help":
      options.help = true;
      break;
    default:
      break;
  }
});

if (options.help) {
  var helpMessage =
    "\nUsage: mutool run unstamp.js [options]\n\n" +
    "Options:\n" +
    "  -i, --input <filename>   Specify input filename\n" +
    "  -o, --output <filename>  Specify output filename\n" +
    "  -k, --kill <content>     Specify the content to remove\n" +
    "  -r, --remove <object>    Specify the object to remove\n" +
    "  -p, --page <pageNum>     Specify the zero based page number to remove\n" +
    "  -d, --debug              Enable debugging\n" +
    "  -s, --silent             Disable logging\n" +
    "  -h, --help               Display this help message\n";

  console.log(helpMessage);
} else {
  try {
    if (options.debug && options.silent) {
      throw new Error(
        "Cannot enable debugging and disable logging at the same time."
      );
    }
    if (options.input) {
      var input = new PDFDocument(options.input);
      var output = options.output != null ? options.output : options.input;
      if (options.kill != null) {
        removeText(input, options.kill);
      }
      if (options.remove != null) {
        removeObject(input, options.remove);
      }
      if (options.page != null) {
        removePage(input, options.page);
      }
      input.save(output, "compress,compress-images,garbage");
    } else {
      throw new Error("No input file");
    }
  } catch (e) {
    console.error(e);
  }
}
