# Journey Micro Animations

Pure HTML + CSS keyframe micro animations for the Coded Graphic WordPress block.

Each animation has its own folder:

- `<name>.html`: the markup fragment (inline SVG)
- `<name>.css`: its styles and keyframes

Images are not kept here: they are hosted on Cloudinary and linked by URL,
and WordPress imports them into the media library.

Every animation runs on one `--cycle` whose first and last frames are the finished
graphic, so it loops without a jump and play-once / reduced motion end on it.
See [AGENTS.md](AGENTS.md) for the motion rules and what the block allows.

| Folder | Description |
| --- | --- |
| `deploy-product-customer/` | Customer on a call, connected to AI, IVR/IVA, Live Agent, Payments, eSignatures, Passkeys, eForms and OTP (design width 786) |
