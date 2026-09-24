/* Site settings. Edit and commit; the site redeploys on its own. */
window.RUNWAY_CONFIG = {
  /* e.g. "https://github.com/your-handle/app-conference-runway" — turns on the "Suggest a fix" button */
  repo: "https://github.com/MBKarasin/app-conference-runway",
  requestEmail: "mark.karasin@protonmail.com",
  curator: "Dr. Mark Karasin",
  credentials: "DNP, APN, RN, AGACNP-BC, CNOR(E)",
  roles: [
    { label: "Primary affiliation", institution: "Rutgers School of Nursing", institutionUrl: "https://nursing.rutgers.edu/", title: "Program Director, Adult-Gerontology Acute Care Nurse Practitioner (AGACNP)", titleLines: ["Program Director", "Adult-Gerontology Acute Care", "Nurse Practitioner (AGACNP)"], titleUrl: "https://nursing.rutgers.edu/academics-admissions/graduate/dnp/adultgerontologyacute/" },
    { label: "Clinical affiliation", institution: "Robert Wood Johnson University Hospital", institutionUrl: "https://www.rwjbh.org/robert-wood-johnson-university-hospital/", title: "Clinical Practice, Advanced Practice Nurse, Division of Cardiothoracic Surgery", titleLines: ["Clinical Practice", "Advanced Practice Nurse", "Division of Cardiothoracic Surgery"] }
  ],
  /* Official logo files go in site/assets/logos/ with these names. Until a file is there, the text link shows alone. */
  partners: []
};
