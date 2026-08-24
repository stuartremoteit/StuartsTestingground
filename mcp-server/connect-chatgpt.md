# Connect ChatGPT

ChatGPT can use the remote.it MCP server as a **custom connector**. Once added, you can ask ChatGPT about your devices, open connections, and run the same operations available in the [web portal](https://app.remote.it).

{% hint style="warning" %}
**Preview release.** The MCP server is currently at:

```
https://mcp.demo.remote.it/mcp
```

This URL will change when the server is fully released. When it does, **delete the connector and add it again** rather than editing it — changing the URL on an existing connector does not reliably re-run tool discovery or the OAuth consent step.
{% endhint %}

## Before you start

* A **remote.it account** — [sign up free](https://app.remote.it/#/sign-up).
* A **ChatGPT plan that includes Developer mode.** Custom MCP connectors are not available on the Free plan. On Business, Enterprise, and Edu workspaces a workspace admin must allow custom connectors before the option appears for you.
* **ChatGPT on the web.** Developer mode is configured in the web app. Once a connector is added there, it may also be usable in ChatGPT's other apps.

<!-- TODO(review): confirm the Plus/Pro vs Business/Enterprise/Edu write-access split below against our own testing before merge. Sourced from third-party reporting, and OpenAI is still rolling this out. -->

{% hint style="warning" %}
**What you can do depends on your plan.** Developer mode is offered on Plus, Pro, Business, Enterprise, and Edu — but the operations you can actually run differ. Plus and Pro are currently limited to read-style operations. Full MCP support, including operations that change something (opening connections, editing, deleting), is rolling out on Business, Enterprise, and Edu.

On Plus or Pro, expect the read-only example in Step 5 to work and the write examples to be unavailable.
{% endhint %}

{% hint style="info" %}
OpenAI has moved this feature and renamed parts of it more than once ("connectors" → "apps" → "plugins"). If a menu below isn't where we say it is, check the other locations listed in [Troubleshooting](#troubleshooting).
{% endhint %}

## Step 1 — Turn on Developer mode

1. Open ChatGPT on the web and go to **Settings**.
2. Select **Security and login**.
3. Turn on **Developer mode**.

If you don't see the toggle, see [Troubleshooting](#troubleshooting).

## Step 2 — Add the remote.it connector

1. Go to the **ChatGPT Plugins** page.
2. Select the **+** button.
3. Fill in the connector details:

   | Field | Value |
   | --- | --- |
   | Name | `remote.it` |
   | Description | `Manage remote.it devices, connections, services, and networks.` |
   | MCP server URL | `https://mcp.demo.remote.it/mcp` |
   | Authentication | OAuth |

4. Create the connection. ChatGPT connects to the server and lists the tools it discovered. Compare this list against the [Tool Reference](/mcp-server/tools.md) — if it's empty or much shorter than expected, the connection didn't complete.

{% hint style="info" %}
The description is not cosmetic — ChatGPT reads it when deciding whether the connector is relevant to your question. Keep it specific about what remote.it does.
{% endhint %}

## Step 3 — Sign in to remote.it

The first time ChatGPT uses a remote.it tool, it opens a browser sign-in. Sign in with your normal remote.it account (social sign-in and 2FA both work), then review the consent screen and choose what to grant. You can restrict the connector to read-only access here — see [Permissions & Safety](/mcp-server/permissions-and-safety.md).

You never paste an API key or secret into ChatGPT.

## Step 4 — Enable the connector in a chat

Adding a connector does **not** switch it on. It has to be selected per conversation.

1. Start a new chat.
2. Select the **+** next to the message box, or open the Developer mode tool in the composer.
3. Choose **remote.it**.

The connector stays active for the rest of that conversation. New conversations start with it off again.

## Step 5 — Test it

Ask something that can only be answered from your account:

* "List my remote.it devices and tell me which are offline."
* "What services are configured on my jump box?"
* "Open an SSH connection to my office Raspberry Pi."

The first is read-only, safe for a first test, and works on every plan that supports Developer mode. If the device names match your actual account, the connector is working. The last example changes something, so it depends on your plan having write access — see [Before you start](#before-you-start).

Where write operations are available to you, ChatGPT asks you to confirm before it runs any tool that writes or changes something, and remote.it adds its own confirmation gate on destructive operations such as deleting devices or running scripts. Expect two prompts on those, not one.

## Limits worth knowing

* **Remote servers only.** ChatGPT cannot reach a server on your laptop or private network. The remote.it MCP server is hosted, so this is not a problem here.
* **Write access is plan-dependent.** See [Before you start](#before-you-start).
* **Deep research mode is different.** In deep research, ChatGPT only uses `search` and `fetch`-style tools, not the full remote.it tool set — this applies even with Developer mode on. Use a normal chat for device operations.
* **Per-chat activation.** See Step 4. This is the single most common reason people think the connector is broken.
* **Custom connectors are not verified by OpenAI.** ChatGPT will warn you about this when you add one. It applies to every custom connector, remote.it included.

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| No **Developer mode** toggle in Settings → Security and login | Check **Settings → Connectors → Advanced settings** and **Settings → Apps → Advanced settings** — OpenAI has used all three locations. If it's absent everywhere, you're on a plan without it, or a workspace admin has disabled custom MCP connectors (Workspace Settings → Permissions & Roles → Connected Data). |
| Connector saves but no tools are listed | The URL is wrong or missing the `/mcp` path. It must be exactly `https://mcp.demo.remote.it/mcp`. |
| Connector added but ChatGPT says it has no remote.it tools | The connector isn't enabled in this conversation. See Step 4. |
| Tools are listed, but ChatGPT won't run one that changes something | Your plan may not include write access. Plus and Pro are currently limited to read-style operations — see [Before you start](#before-you-start). |
| Sign-in loops or never completes | Complete the browser sign-in in the same browser profile you're using for ChatGPT, then retry the prompt. |
| ChatGPT sits silently after proposing a tool call | It's waiting on your confirmation. Approve or reject the call in the chat. |
| Tools appear but calls fail with a permissions error | Your remote.it account or the scopes you granted at consent don't cover that operation. Review [Permissions & Safety](/mcp-server/permissions-and-safety.md), or disconnect and reconnect to re-run the consent screen. |

## Next steps

* [Tool Reference](/mcp-server/tools.md) — every tool the server exposes
* [Permissions & Safety](/mcp-server/permissions-and-safety.md) — scopes, consent, and safety gates
* [Connect Grok](/mcp-server/connect-grok.md)
* [Connect Claude](/mcp-server/connect-claude.md)
