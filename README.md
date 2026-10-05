# Journey Micro Animations

Pure HTML + CSS keyframe micro animations for the Coded Graphic WordPress block.

Each animation has its own folder:

- `<name>.html`: the markup fragment (inline SVG)
- `<name>.css`: its styles and keyframes

Images are not kept here: they are hosted on Cloudinary and linked by URL,
and WordPress imports them into the media library.

Every animation builds once on one `--cycle` whose first and last frames are the
finished graphic, so play-once and reduced motion end on it; only live parts loop.
See [AGENTS.md](AGENTS.md) for the motion rules and what the block allows, and
the `micro-animation` skill in `.claude/skills/` for how to build one (with a
lint, photo prep and render scripts).

| Folder | Description |
| --- | --- |
| `deploy-product-customer/` | Customer on a call, connected to AI, IVR/IVA, Live Agent, Payments, eSignatures, Passkeys, eForms and OTP (design width 786) |
| `get-demo/` | Agent with headset inside three rings of product badges (design width 1000) |
| `featured-image-payments/` | Agent call window confirming each payment step in turn beside the customer's phone, ending on "Payment confirmed" (design width 1216) |
| `password-reset-flow/` | Password reset request, SMS and Face ID arriving in step with the agent window confirming each step, ending on "Success" (design width 1624) |
| `agent-general-workflows/` | Agent photo with the channel icons growing in down the left then the right, then the Password Reset, passkey Sign In and DTMF cards coming in one after another (design width 1304) |
| `featured-image-products/` | Photo of a man holding a phone; the bars on either side draw out from behind it one by one, then the Authentication, Documents, Payments and Flexible Workflows cards come in once. With Loop on, only the bars keep drawing in and out (design width 1216) |
| `ai-mcp/` | Agent bot with its tools, MCP and the Journey node branching to three servers, built once top to bottom; with Loop on, only the bars behind MCP keep drawing in and out (design width 1140) |
