
const API_URL = "http://127.0.0.1:8000";

let generatedContent = "";
let generatedTopic = "";
let generatedType = "";

// Generate AI content
async function generateContent() {
    const topic = document.getElementById("topic").value.trim();
    const contentType = document.getElementById("contentType").value;
    const button = document.getElementById("generateBtn");
    const message = document.getElementById("message");
    const resultBox = document.getElementById("resultBox");

    if (!topic) {
        message.textContent = "Please enter a topic first.";
        return;
    }

    button.disabled = true;
    button.textContent = "Generating...";
    message.textContent = "AI is generating content...";
    resultBox.classList.add("hidden");

    try {
        const response = await fetch(`${API_URL}/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                topic: topic,
                content_type: contentType
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Generation failed");
        }

        generatedContent = data.generated_content;
        generatedTopic = topic;
        generatedType = contentType;

        document.getElementById("result").textContent =
            generatedContent;

        resultBox.classList.remove("hidden");
        message.textContent = "Content generated successfully!";

    } catch (error) {
        message.textContent = "Error: " + error.message;
    } finally {
        button.disabled = false;
        button.textContent = "✦ Generate Instagram Content";
    }
}

// Copy generated content
function copyContent() {
    if (!generatedContent) return;

    navigator.clipboard.writeText(generatedContent)
        .then(() => {
            document.getElementById("message").textContent =
                "Content copied!";
        })
        .catch(() => {
            document.getElementById("message").textContent =
                "Copy failed. Select and copy manually.";
        });
}

// Save post permanently in SQLite
async function saveForApproval() {
    if (!generatedContent) {
        alert("Generate content first.");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/posts`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                topic: generatedTopic,
                content_type: generatedType,
                content: generatedContent
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Could not save post");
        }

        document.getElementById("message").textContent =
            "Post saved permanently for approval!";

        generatedContent = "";
        document.getElementById("resultBox").classList.add("hidden");

        await loadPosts();

    } catch (error) {
        document.getElementById("message").textContent =
            "Save error: " + error.message;
    }
}

// Load posts from SQLite
async function loadPosts() {
    try {
        const response = await fetch(`${API_URL}/posts`);

        if (!response.ok) {
            throw new Error("Could not load posts");
        }

        const posts = await response.json();

        const postList = document.getElementById("postList");
        postList.replaceChildren();

        let pending = 0;

        posts.forEach(post => {
            if (post.status === "pending") pending++;

            const item = document.createElement("div");
            item.className = "post-item";

            const title = document.createElement("h3");
            title.textContent = post.topic;

            const status = document.createElement("strong");
            status.textContent = post.status.toUpperCase();

            const content = document.createElement("textarea");
content.value = post.content;
content.rows = 7;
content.style.width = "100%";
content.style.marginTop = "12px";
content.style.padding = "12px";
content.style.border = "1px solid #ddd";
content.style.borderRadius = "8px";

            const actions = document.createElement("div");
            actions.style.marginTop = "12px";

            if (post.status === "pending") {
                const approve = document.createElement("button");
                approve.textContent = "Approve";
                approve.style.background = "#16834b";
                approve.style.color = "white";
                approve.onclick = () =>
                    updateStatus(post.id, "approved");

                const reject = document.createElement("button");
                reject.textContent = "Reject";
                reject.style.marginLeft = "8px";
                reject.onclick = () =>
                    updateStatus(post.id, "rejected");

                actions.append(approve, reject);
            }

            const remove = document.createElement("button");
            remove.textContent = "Delete";
            remove.style.marginLeft = "8px";
            remove.onclick = () => deletePost(post.id);

            actions.appendChild(remove);

           const editButton = document.createElement("button");
editButton.textContent = "Save Changes";
editButton.style.marginTop = "10px";
editButton.onclick = () => editPost(post.id, content.value);

item.append(title, status, content, editButton, actions);
            postList.appendChild(item);
        });

        document.getElementById("totalPosts").textContent =
            posts.length;

        document.getElementById("pendingPosts").textContent =
            pending;

    } catch (error) {
        console.error("Post loading error:", error);
    }
}

// Approve or reject post
async function updateStatus(id, status) {
    try {
        const response = await fetch(
            `${API_URL}/posts/${id}/status`,
            {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: status })
            }
        );

        if (!response.ok) throw new Error("Status update failed");

        await loadPosts();
    } catch (error) {
        alert(error.message);
    }
}

// Delete post
async function deletePost(id) {
    if (!confirm("Are you sure you want to delete this post?")) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/posts/${id}`, {
            method: "DELETE"
        });

        if (!response.ok) throw new Error("Delete failed");

        await loadPosts();
    } catch (error) {
        alert(error.message);
    }
}

// Load saved posts when dashboard opens
document.addEventListener("DOMContentLoaded", loadPosts);
async function editPost(id, content) {

    if (!content.trim()) {
        alert("Caption cannot be empty.");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/posts/${id}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                content: content
            })
        });

        if (!response.ok) {
            throw new Error("Could not update caption");
        }

        alert("Caption updated successfully!");

        await loadPosts();

    } catch (error) {
        alert(error.message);
    }
}
// Instagram Image Creator
async function createInstagramImage() {

    const topic = document.getElementById("imageTopic").value.trim();
    const title = document.getElementById("imageTitle").value.trim();
    const subtitle = document.getElementById("imageSubtitle").value.trim();

    const button = document.getElementById("createImageBtn");
    const message = document.getElementById("imageMessage");
    const previewBox = document.getElementById("imagePreviewBox");
    const image = document.getElementById("generatedImage");
    const downloadLink = document.getElementById("downloadImage");

    if (!topic || !title || !subtitle) {
        message.textContent = "Please fill in all fields.";
        return;
    }

    button.disabled = true;
    button.textContent = "Creating Image...";
    message.textContent = "InstaAI is creating your image...";
    previewBox.classList.add("hidden");

    try {
        const response = await fetch(`${API_URL}/create-image`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                topic: topic,
                title: title,
                subtitle: subtitle
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Image generation failed.");
        }

        const imageUrl = `${API_URL}${data.image_url}`;

        image.onload = function () {
            previewBox.classList.remove("hidden");
            message.textContent = "Image created successfully!";
        };

        image.onerror = function () {
            message.textContent = "Image created, but preview could not load.";
        };

        image.src = imageUrl;

        downloadLink.href = imageUrl;
        downloadLink.download = "InstaAI_Post.png";

    } catch (error) {
        message.textContent = "Image error: " + error.message;
    } finally {
        button.disabled = false;
        button.textContent = "🎨 Generate Instagram Image";
    }
}
// InstaAI Image Creator
window.createInstagramImage = async function () {

    const topic = document.getElementById("imageTopic").value.trim();
    const title = document.getElementById("imageTitle").value.trim();
    const subtitle = document.getElementById("imageSubtitle").value.trim();

    const button = document.getElementById("createImageBtn");
    const message = document.getElementById("imageMessage");
    const preview = document.getElementById("imagePreviewBox");
    const image = document.getElementById("generatedImage");
    const download = document.getElementById("downloadImage");

    if (!topic || !title || !subtitle) {
        message.textContent = "Please fill in all fields.";
        return;
    }

    button.disabled = true;
    button.textContent = "Creating Image...";
    message.textContent = "InstaAI is creating your image...";

    try {
        const response = await fetch(`${API_URL}/create-image`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                topic: topic,
                title: title,
                subtitle: subtitle
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Image generation failed");
        }

        const imageUrl = `${API_URL}${data.image_url}`;

        image.onload = function () {
            preview.classList.remove("hidden");
            message.textContent = "Image created successfully!";
        };

        image.onerror = function () {
            message.textContent = "Image was created, but preview failed to load.";
        };

        image.src = imageUrl;
        download.href = imageUrl;
        download.download = "InstaAI_Post.png";

    } catch (error) {
        message.textContent = "Error: " + error.message;
    } finally {
        button.disabled = false;
        button.textContent = "🎨 Generate Instagram Image";
    }
};

// ======================================
// InstaAI - AI Carousel Creator
// ======================================


// ======================================
// InstaAI - Professional AI Carousel Creator
// ======================================

window.createCarousel = async function () {
    const topic = document.getElementById("carouselTopic").value.trim();
    const slideCount = Number(
        document.getElementById("carouselSlideCount").value
    );

    const button = document.getElementById("createCarouselBtn");
    const message = document.getElementById("carouselMessage");
    const preview = document.getElementById("carouselPreview");

    if (!topic) {
        message.textContent = "Please enter a carousel topic.";
        return;
    }

    if (slideCount < 3 || slideCount > 7) {
        message.textContent = "Please select between 3 and 7 slides.";
        return;
    }

    button.disabled = true;
    button.textContent = "Generating Carousel...";
    message.textContent = "Qwen AI is creating your slides. Please wait...";
    preview.replaceChildren();

    try {
        const response = await fetch(`${API_URL}/create-carousel`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                topic: topic,
                slide_count: slideCount
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Carousel generation failed.");
        }

        if (!data.images || data.images.length !== slideCount) {
            throw new Error("Carousel images are incomplete.");
        }

        // Professional responsive grid
        const grid = document.createElement("div");
        grid.style.display = "grid";
        grid.style.gridTemplateColumns =
            "repeat(auto-fit, minmax(220px, 1fr))";
        grid.style.gap = "20px";
        grid.style.width = "100%";
        grid.style.marginTop = "20px";

        data.images.forEach((imagePath, index) => {
            const imageUrl = `${API_URL}${imagePath}`;
            const slide = data.slides[index];

            const card = document.createElement("div");
            card.style.background = "#ffffff";
            card.style.padding = "14px";
            card.style.borderRadius = "14px";
            card.style.border = "1px solid #e5e7eb";
            card.style.boxShadow = "0 4px 14px rgba(0,0,0,0.06)";
            card.style.minWidth = "0";

            const heading = document.createElement("h3");
            heading.textContent = `Slide ${index + 1}`;
            heading.style.marginBottom = "10px";

            const image = document.createElement("img");
            image.src = imageUrl;
            image.alt = `Carousel slide ${index + 1}`;
            image.loading = "lazy";
            image.style.width = "100%";
            image.style.aspectRatio = "1 / 1";
            image.style.objectFit = "contain";
            image.style.borderRadius = "10px";
            image.style.display = "block";

            const title = document.createElement("h4");
            title.textContent = slide.title;
            title.style.marginTop = "12px";

            const subtitle = document.createElement("p");
            subtitle.textContent = slide.subtitle;
            subtitle.style.color = "#666";
            subtitle.style.fontSize = "13px";

            const download = document.createElement("a");
            download.href = imageUrl;
            download.download =
                `InstaAI_Carousel_Slide_${index + 1}.png`;
            download.textContent = "⬇ Download Slide";
            download.style.display = "inline-block";
            download.style.marginTop = "12px";
            download.style.padding = "9px 14px";
            download.style.background = "#7048e8";
            download.style.color = "#ffffff";
            download.style.borderRadius = "8px";
            download.style.textDecoration = "none";
            download.style.fontWeight = "bold";
            download.style.fontSize = "13px";

            card.append(heading, image, title, subtitle, download);
            grid.appendChild(card);
        });

        preview.appendChild(grid);
        
        // Download all carousel slides as ZIP
        const zipButton = document.createElement("button");

        zipButton.textContent = "📦 Download All Slides (ZIP)";
        zipButton.style.display = "block";
        zipButton.style.marginTop = "25px";
        zipButton.style.padding = "14px 22px";
        zipButton.style.background = "#16834b";
        zipButton.style.color = "#ffffff";
        zipButton.style.border = "none";
        zipButton.style.borderRadius = "9px";
        zipButton.style.fontWeight = "bold";
        zipButton.style.cursor = "pointer";

        zipButton.onclick = async function () {
            zipButton.disabled = true;
            zipButton.textContent = "Preparing ZIP...";

            try {
                const zipResponse = await fetch(
                    `${API_URL}/download-carousel-zip`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            images: data.images
                        })
                    }
                );

                if (!zipResponse.ok) {
                    const errorData = await zipResponse.json();
                    throw new Error(
                        errorData.detail || "ZIP download failed."
                    );
                }

                const blob = await zipResponse.blob();
                const downloadUrl = URL.createObjectURL(blob);

                const link = document.createElement("a");
                link.href = downloadUrl;
                link.download = "InstaAI_Carousel.zip";

                document.body.appendChild(link);
                link.click();
                link.remove();

                URL.revokeObjectURL(downloadUrl);

                message.textContent =
                    "Your carousel ZIP is ready!";

            } catch (error) {
                message.textContent =
                    "ZIP error: " + error.message;
            } finally {
                zipButton.disabled = false;
                zipButton.textContent =
                    "📦 Download All Slides (ZIP)";
            }
        };

        preview.appendChild(zipButton);

        message.textContent =
            `Successfully created ${data.images.length} carousel slides!`;

    } catch (error) {
        message.textContent = "Carousel error: " + error.message;
    } finally {
        button.disabled = false;
        button.textContent = "🎠 Generate Instagram Carousel";
    }
};

// ======================================
// InstaAI - AI Reel Script Generator
// ======================================

let generatedReelScript = "";

window.generateReelScript = async function () {

    const topic = document.getElementById("reelTopic").value.trim();
    const duration = Number(
        document.getElementById("reelDuration").value
    );
    const language = document.getElementById("reelLanguage").value;

    const button = document.getElementById("generateReelBtn");
    const message = document.getElementById("reelMessage");
    const resultBox = document.getElementById("reelResultBox");
    const result = document.getElementById("reelResult");

    if (!topic) {
        message.textContent = "Please enter a Reel topic.";
        return;
    }

    button.disabled = true;
    button.textContent = "Generating Reel Script...";
    message.textContent = "Qwen AI is writing your Reel script...";
    resultBox.classList.add("hidden");

    try {
        const response = await fetch(
            `${API_URL}/generate-reel-script`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    topic: topic,
                    duration: duration,
                    language: language
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Reel script generation failed."
            );
        }

        generatedReelScript = data.generated_script;

        result.textContent = generatedReelScript;
        resultBox.classList.remove("hidden");

        message.textContent = "Reel script generated successfully!";

    } catch (error) {
        message.textContent = "Error: " + error.message;

    } finally {
        button.disabled = false;
        button.textContent = "🎬 Generate Reel Script";
    }
};


// Copy generated Reel script
window.copyReelScript = async function () {

    if (!generatedReelScript) {
        alert("Generate a Reel script first.");
        return;
    }

    try {
        await navigator.clipboard.writeText(generatedReelScript);

        document.getElementById("reelMessage").textContent =
            "Reel script copied successfully!";

    } catch (error) {
        document.getElementById("reelMessage").textContent =
            "Copy failed. Please select and copy manually.";
    }
};

window.generateVoiceover = async function () {
    const text = document.getElementById("voiceoverText").value.trim();
    const voice = document.getElementById("voiceoverVoice").value;
    const rate = Number(document.getElementById("voiceoverRate").value);

    const button = document.getElementById("generateVoiceoverBtn");
    const message = document.getElementById("voiceoverMessage");
    const resultBox = document.getElementById("voiceoverResult");
    const player = document.getElementById("voiceoverPlayer");
    const download = document.getElementById("downloadVoiceover");

    if (!text) {
        message.textContent = "Please enter your voiceover text.";
        return;
    }

    button.disabled = true;
    button.textContent = "Generating voiceover...";
    message.textContent = "Please wait. Your local AI voice is working.";

    resultBox.classList.add("hidden");

    try {
        const response = await fetch(`${API_URL}/generate-voiceover`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                text: text,
                voice: voice,
                rate: rate
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Voiceover generation failed");
        }

        const audioUrl = `${API_URL}${data.audio_url}`;

        player.src = audioUrl;
        download.href = audioUrl;

        resultBox.classList.remove("hidden");
        message.textContent = "Voiceover generated successfully!";

    } catch (error) {
        message.textContent = "Error: " + error.message;
    } finally {
        button.disabled = false;
        button.textContent = "🎙️ Generate Voiceover";
    }
};

// InstaAI - Automatic Reel Video Creator

window.createAutomaticReel = async function () {

    const topic = document.getElementById("autoReelTopic").value.trim();
    const narration = document.getElementById("autoReelNarration").value.trim();
    const voice = document.getElementById("autoReelVoice").value;
    const rate = Number(document.getElementById("autoReelRate").value);

    const button = document.getElementById("createAutomaticReelBtn");
    const message = document.getElementById("autoReelMessage");
    const resultBox = document.getElementById("autoReelResult");
    const player = document.getElementById("autoReelPlayer");
    const download = document.getElementById("downloadAutoReel");

    if (!topic || !narration) {
        message.textContent = "Please enter both topic and narration.";
        return;
    }

    button.disabled = true;
    resultBox.classList.add("hidden");
    message.textContent = "Step 1/2: Generating AI voiceover...";

    try {

        // Step 1: Generate voiceover
        const voiceResponse = await fetch(`${API_URL}/generate-voiceover`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                text: narration,
                voice: voice,
                rate: rate
            })
        });

        const voiceData = await voiceResponse.json();

        if (!voiceResponse.ok) {
            throw new Error(voiceData.detail || "Voiceover generation failed");
        }

        const audioFilename = voiceData.audio_url.split("/").pop();

        // Step 2: Generate MP4 video
        message.textContent = "Step 2/2: Creating your Instagram Reel. Please wait...";

        const videoResponse = await fetch(`${API_URL}/create-reel-video`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                topic: topic,
                narration: narration,
                audio_filename: audioFilename
            })
        });

        const videoData = await videoResponse.json();

        if (!videoResponse.ok) {
            throw new Error(videoData.detail || "Video generation failed");
        }

        const videoUrl = `${API_URL}${videoData.video_url}`;

        player.src = videoUrl;
        player.load();

        download.href = videoUrl;

        resultBox.classList.remove("hidden");
        message.textContent = "Success! Your Instagram Reel is ready.";

    } catch (error) {

        message.textContent = "Error: " + error.message;

    } finally {

        button.disabled = false;
        button.textContent = "🎥 Generate Complete Instagram Reel";

    }
};

// ======================================
// InstaAI - Reel Batch Review & Approval
// ======================================

let activeReelBatchId = "";

function mediaUrlFromPath(filePath) {
    if (!filePath) return "";
    const filename = String(filePath)
        .replaceAll("\\", "/")
        .split("/")
        .pop();

    return `${API_URL}/media/videos/${encodeURIComponent(filename)}`;
}

// Load all Reel batches
window.loadReelBatches = async function () {
    const select = document.getElementById("batchSelect");
    const message = document.getElementById("batchMessage");
    const refreshButton = document.getElementById("refreshBatchesBtn");

    if (!select || !message) return;

    if (refreshButton) refreshButton.disabled = true;

    message.textContent = "Loading Reel batches...";

    try {
        const response = await fetch(`${API_URL}/reel-batches`);
        const batches = await response.json();

        if (!response.ok) {
            throw new Error(batches.detail || "Could not load batches");
        }

        select.replaceChildren();

        if (!batches.length) {
            select.add(new Option("No batches found", ""));
            activeReelBatchId = "";

            document.getElementById("reelBatchList").replaceChildren();

            document.getElementById("batchSummary").textContent =
                "Create a Reel batch to see it here.";

            setBatchActionState(false);
            message.textContent = "No Reel batches found yet.";
            return;
        }

        batches.forEach(batch => {
            const label =
                `${batch.id} — ${batch.status} (${batch.reel_count}/${batch.target_count})`;

            select.add(new Option(label, batch.id));
        });

        const readyBatch =
            batches.find(batch => batch.status === "ready") || batches[0];

        activeReelBatchId = readyBatch.id;
        select.value = activeReelBatchId;

        await loadSelectedReelBatch();

    } catch (error) {
        message.textContent = "Batch loading error: " + error.message;
        setBatchActionState(false);

    } finally {
        if (refreshButton) refreshButton.disabled = false;
    }
};


// Load selected batch and display video previews
async function loadSelectedReelBatch() {

    const select = document.getElementById("batchSelect");
    const message = document.getElementById("batchMessage");
    const grid = document.getElementById("reelBatchList");
    const summary = document.getElementById("batchSummary");

    activeReelBatchId = select.value;

    if (!activeReelBatchId) return;

    message.textContent = "Loading Reel previews...";
    grid.replaceChildren();

    try {
        const response = await fetch(
            `${API_URL}/reel-batches/${encodeURIComponent(activeReelBatchId)}/reels`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Could not load this batch");
        }

        const batch = data.batch;
        const reels = data.reels || [];

        const readyCount = reels.filter(
            reel => reel.status === "ready" || reel.status === "approved"
        ).length;

        summary.textContent =
            `Batch ${batch.id} • ${readyCount} of ${batch.target_count} videos ready • Status: ${batch.status.toUpperCase()}`;

        reels.forEach((reel, index) => {

            const card = document.createElement("article");
            card.className = "reel-review-card";

            const heading = document.createElement("div");
            heading.className = "reel-card-heading";

            const title = document.createElement("h3");
            title.textContent = `Reel ${index + 1}: ${reel.topic}`;

            const badge = document.createElement("span");
            badge.className =
                `reel-status status-${String(reel.status).toLowerCase()}`;

            badge.textContent = String(reel.status).toUpperCase();

            heading.append(title, badge);
            card.appendChild(heading);

            // Video preview
            if (reel.video_path) {

                const video = document.createElement("video");

                video.controls = true;
                video.preload = "metadata";
                video.playsInline = true;
                video.src = mediaUrlFromPath(reel.video_path);

                card.appendChild(video);

            } else {

                const waiting = document.createElement("p");

                waiting.className = "reel-waiting";

                waiting.textContent = reel.error
                    ? `Generation error: ${reel.error}`
                    : "Video is not ready yet.";

                card.appendChild(waiting);
            }

            // Narration
            const narrationLabel = document.createElement("strong");
            narrationLabel.textContent = "Narration";

            const narration = document.createElement("p");
            narration.className = "reel-narration";

            narration.textContent =
                reel.narration || "Narration is being generated...";

            card.append(narrationLabel, narration);

            // Audio preview
            if (reel.audio_path) {

                const audio = document.createElement("audio");
                audio.controls = true;
                audio.preload = "none";

                const audioName = String(reel.audio_path)
                    .replaceAll("\\", "/")
                    .split("/")
                    .pop();

                audio.src =
                    `${API_URL}/media/${encodeURIComponent(audioName)}`;

                card.appendChild(audio);
            }

            grid.appendChild(card);
        });

        const allReady =
            reels.length === Number(batch.target_count) &&
            reels.every(reel => reel.status === "ready");

        const isPending =
            batch.status === "ready" || batch.status === "pending";

        setBatchActionState(allReady && isPending);

        message.textContent = allReady
            ? "All Reels are ready for your review. Watch them before approving."
            : `Batch is ${batch.status}. ${readyCount}/${batch.target_count} Reels are ready.`;

    } catch (error) {

        message.textContent = "Preview error: " + error.message;
        setBatchActionState(false);
    }
}


// Enable or disable batch buttons
function setBatchActionState(enabled) {

    const approve = document.getElementById("approveBatchBtn");
    const reject = document.getElementById("rejectBatchBtn");

    if (approve) approve.disabled = !enabled;
    if (reject) reject.disabled = !enabled;
}


// Initialize batch dashboard
document.addEventListener("DOMContentLoaded", () => {

    const select = document.getElementById("batchSelect");

    if (select) {
        select.addEventListener("change", loadSelectedReelBatch);
    }

    loadReelBatches();
});


// Approve all Reels
window.approveReelBatch = async function () {

    if (!activeReelBatchId) return;

    if (!confirm("Approve all six Reels in this batch? Review every video before continuing.")) {
        return;
    }

    const button = document.getElementById("approveBatchBtn");
    button.disabled = true;

    try {

        const response = await fetch(
            `${API_URL}/reel-batches/${encodeURIComponent(activeReelBatchId)}/approve-all`,
            { method: "POST" }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Batch approval failed");
        }

        document.getElementById("batchMessage").textContent =
            "Batch approved successfully. No Instagram post has been published.";

        await loadReelBatches();

    } catch (error) {

        document.getElementById("batchMessage").textContent =
            "Approval error: " + error.message;

        button.disabled = false;
    }
};


// Reject all Reels
window.rejectReelBatch = async function () {

    if (!activeReelBatchId) return;

    if (!confirm("Reject all Reels in this batch?")) {
        return;
    }

    const button = document.getElementById("rejectBatchBtn");
    button.disabled = true;

    try {

        const response = await fetch(
            `${API_URL}/reel-batches/${encodeURIComponent(activeReelBatchId)}/reject-all`,
            { method: "POST" }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Batch rejection failed");
        }

        document.getElementById("batchMessage").textContent =
            "The batch has been rejected.";

        await loadReelBatches();

    } catch (error) {

        document.getElementById("batchMessage").textContent =
            "Rejection error: " + error.message;

        button.disabled = false;
    }
};
