async function loadPatientList() {
  const res = await fetch("/api/patients");
  const patients = await res.json();
  const list = document.getElementById("patientListItems");
  list.innerHTML = "";
  patients.forEach(p => {
    const li = document.createElement("li");
    li.textContent = `${p.patient_id} - ${p.full_name}`;
    list.appendChild(li);
  });
}

async function searchPatient() {
  const query = document.getElementById("searchInput").value;
  const res = await fetch(`/api/patients/search?query=${encodeURIComponent(query)}`);
  const results = await res.json();

  if (results.length === 0) {
    alert("Không tìm thấy bệnh nhân.");
    return;
  }

  const patient = results[0];
  document.getElementById("patientInfo").textContent =
    `${patient.full_name} (${patient.patient_id}) - ${patient.birth_date}`;
  document.getElementById("patientPanel").style.display = "block";

  window.currentPatientId = patient.patient_id;
}

async function showObservation(type) {
  const patientId = window.currentPatientId;
  const res = await fetch(`/api/observations/${patientId}`);
  const data = await res.json();
  const filtered = data.filter(o => o.type === type);

  const valueDiv = document.getElementById("observationValue");
  valueDiv.innerHTML = filtered.map(o => `${o.date}: ${o.value}`).join("<br>");

  // TODO: Vẽ biểu đồ bằng Chart.js nếu cần
}

window.onload = loadPatientList;
