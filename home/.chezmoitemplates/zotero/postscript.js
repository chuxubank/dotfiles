if (
  Translator.BetterTeX &&
  !Translator.options.exportFileData &&
  zotero.attachments &&
  zotero.attachments.length
) {
  for (const att of zotero.attachments) {
    if (att.localPath) {
      att.localPath = att.localPath.replace(RegExp("^\/.*?\/.*?\/"), "~/");
    }
  }
  tex.add({ name: "file", value: zotero.attachments, enc: "attachments" });
  return { cache: false };
}
