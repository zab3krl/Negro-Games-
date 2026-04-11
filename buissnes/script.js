const downloadBtn = document.getElementById("downloadBtn");
const statusLine = document.getElementById("status");

const launcherUrl = "downloads/NegroGamesLauncherSetup.exe";
let cooldown = 0;
let timer = null;

function updateButtonText() {
  if (cooldown > 0) {
    downloadBtn.textContent = `Pobieranie za ${cooldown}s`;
    downloadBtn.disabled = true;
  } else {
    downloadBtn.textContent = "pobierz na Windows";
    downloadBtn.disabled = false;
  }
}

function startDownload() {
  const link = document.createElement("a");
  link.href = launcherUrl;
  link.download = "NegroGamesLauncherSetup.exe";
  document.body.appendChild(link);
  link.click();
  link.remove();
}

downloadBtn.addEventListener("click", () => {
  if (cooldown > 0) {
    return;
  }

  statusLine.textContent = "Przygotowuje paczke instalacyjna...";
  cooldown = 3;
  updateButtonText();

  timer = window.setInterval(() => {
    cooldown -= 1;
    updateButtonText();

    if (cooldown <= 0) {
      window.clearInterval(timer);
      startDownload();
      statusLine.innerHTML = "Pobieranie wystartowalo. Jesli nic sie nie dzieje, sprawdz czy plik istnieje pod adresem <strong>downloads/NegroGamesLauncherSetup.exe</strong>.";
    }
  }, 1000);
});

updateButtonText();