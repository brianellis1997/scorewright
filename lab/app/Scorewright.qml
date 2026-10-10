import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MuseScore 3.0

// Scorewright panel for MuseScore Studio 4.7: chat with the Claude Code harness, see suggestions
// arrive, open them in the editor (green bars), accept or reject. Talks to app/server.py on ws://localhost:8791.
MuseScore {
    id: root
    title: "Scorewright"
    description: "Copilot for composers: chat, suggestions, accept/reject"
    version: "0.1"
    pluginType: "dialog"
    requiresScore: false
    width: 420
    height: 640

    property int sock: -1
    property var suggestions: []
    property string status: "connecting…"

    ListModel { id: chatModel }

    function push(who, text, sid) {
        chatModel.append({ who: who, text: text, sid: sid || "" })
        chatView.positionViewAtEnd()
    }
    function send(obj) {
        if (root.sock < 0) { root.status = "not connected"; return }
        api.websocket.send(root.sock, JSON.stringify(obj))
    }
    function onMessage(raw) {
        var m
        try { m = JSON.parse(raw) } catch (e) { push("claude", raw, ""); return }
        if (m.type === "state") {
            chatModel.clear(); root.suggestions = m.suggestions || []
            for (var i = 0; i < (m.chat || []).length; i++) {
                var c = m.chat[i]; push(c.who, c.text, c.suggestion || "")
            }
            root.status = "connected · " + (m.working ? m.working.split("/").pop() : "no working score")
        } else if (m.type === "chat") {
            push(m.who, m.text, "")
        } else if (m.type === "suggestion") {
            var s = root.suggestions.slice(); s.push(m); root.suggestions = s
            push("claude", "Suggestion " + m.id + ": bars " + m.lo + "-" + m.hi + ". " + m.note, m.id)
            if (autoOpen.checked) openSuggestion(m.id)
        } else if (m.type === "verdict") {
            push("brian", (m.accepted ? "Accepted " : "Rejected ") + m.id + (m.text ? ": " + m.text : ""), "")
        } else if (m.type === "working") {
            root.status = "connected · " + m.file.split("/").pop()
        }
    }
    function findSug(id) { for (var i = 0; i < root.suggestions.length; i++) if (root.suggestions[i].id === id) return root.suggestions[i]; return null }
    function openSuggestion(id) {
        var s = findSug(id); if (!s) return
        readScore(s.green)            // opens the green-marked MusicXML as a new tab in MuseScore
        root.status = "opened " + id + " (green bars " + s.lo + "-" + s.hi + ")"
    }
    function connect() {
        api.websocket.open(8791, function(id) {
            root.sock = id
            api.websocket.onMessage(id, root.onMessage)
            root.status = "connected"
            root.send({ type: "state" })
        })
    }
    onRun: { connect() }

    ColumnLayout {
        anchors.fill: parent; anchors.margins: 8; spacing: 6
        RowLayout {
            Label { text: root.status; Layout.fillWidth: true; elide: Text.ElideMiddle }
            CheckBox { id: autoOpen; text: "auto-open"; checked: true }
            Button { text: "reconnect"; onClicked: connect() }
        }
        ListView {
            id: chatView
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 4
            model: chatModel
            delegate: Rectangle {
                width: chatView.width
                radius: 8
                color: sid !== "" ? "#e2f2e7" : (who === "brian" ? "#e4ebff" : "#f1f0ea")
                implicitHeight: col.implicitHeight + 12
                ColumnLayout {
                    id: col; anchors.left: parent.left; anchors.right: parent.right; anchors.margins: 6; spacing: 4
                    Label { text: (who === "brian" ? "you" : "Claude"); font.pixelSize: 10; color: "#777" }
                    Label { text: model.text; wrapMode: Text.Wrap; Layout.fillWidth: true; color: "#111" }
                    RowLayout {
                        visible: sid !== "" && (findSug(sid) ? findSug(sid).status === "open" : false)
                        Button { text: "Open"; onClicked: openSuggestion(sid) }
                        Button { text: "Accept"; onClicked: { root.send({ type: "accept", id: sid, text: verdictBox.text }); verdictBox.text = "" } }
                        Button { text: "Reject"; onClicked: { root.send({ type: "reject", id: sid, text: verdictBox.text }); verdictBox.text = "" } }
                    }
                }
            }
        }
        TextField { id: verdictBox; Layout.fillWidth: true; placeholderText: "why (for accept/reject): the training signal" }
        RowLayout {
            TextArea {
                id: msgBox; Layout.fillWidth: true; Layout.preferredHeight: 70; wrapMode: TextEdit.Wrap
                placeholderText: "talk or type (press the mic key for dictation): continue from bar 24, keep it open…"
                Keys.onReturnPressed: function(ev) { if (!(ev.modifiers & Qt.ShiftModifier)) { sendMsg(); ev.accepted = true } }
            }
            Button { text: "Send"; onClicked: sendMsg() }
        }
    }
    function sendMsg() {
        var t = msgBox.text.trim(); if (!t) return
        root.send({ type: "message", text: t }); msgBox.text = ""
    }
}
