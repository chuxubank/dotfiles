import { CustomEditor, type ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import { matchesKey, parseKey } from "@oh-my-pi/pi-tui";

export default function (pi: ExtensionAPI) {
	pi.setLabel("Emacs C-d EOF");
	pi.on("session_start", (_event, ctx) => {
		if (!ctx.hasUI) return;
		ctx.ui.setEditorComponent((tui, theme, keybindings) => {
			const editor = new CustomEditor(tui, theme, keybindings);
			const handleInput = editor.handleInput.bind(editor);
			editor.handleInput = (data: string) => {
				if (
					(matchesKey(data, "ctrl+d") || parseKey(data) === "ctrl+d") &&
					editor.getText().length === 0 &&
					editor.pendingImages.length === 0 &&
					editor.pendingTexts.length === 0
				) {
					// ExtensionContext.shutdown() only flags a post-turn check.
					// onExit is wired to handleCtrlD → InteractiveMode.shutdown.
					editor.onExit?.();
					return;
				}
				handleInput(data);
			};
			return editor;
		});
	});
}
