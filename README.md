# fonts

Custom builds of programming fonts, each built in a container (podman or docker)
with extra symbols, braille, Nerd Fonts (single width) and terminal metric tuning.

| Dir | Base | Ligatures | Family name |
|---|---|---|---|
| `monofoki/` | [monofoki](https://github.com/datMaffin/monofoki) (Mononoki fork) | Fira Code, baked into the sources | `monofoki` |
| `fantasque-sans/` | [Fantasque Sans Mono](https://github.com/belluzj/fantasque-sans) | the font's own | `Fantasque Sans Mono` |
| `code-new-roman/` | [Code New Roman](https://github.com/sdwolf/CodeNewRoman) | Fira Code, added at build | `Code New Roman` |

Build any of them with `./build.sh` inside its directory (`--install` copies the
result to `~/.local/share/fonts/`; close Emacs first). Output goes to `export/nerd/`.

Each font keeps its own license (SIL OFL 1.1); see the `LICENSE*` files in each dir.
Donor glyphs come from DejaVu Sans Mono and Cascadia Code; icons from Nerd Fonts.
