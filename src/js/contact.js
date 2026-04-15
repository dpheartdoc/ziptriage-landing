document.addEventListener("DOMContentLoaded", function () {
  const forms = document.querySelectorAll("[data-contact-form]");

  forms.forEach(function (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();

      const submitBtn = form.querySelector('button[type="submit"]');
      const statusEl = form.querySelector("[data-form-status]");
      const originalText = submitBtn.textContent;

      submitBtn.disabled = true;
      submitBtn.textContent = "Sending...";
      if (statusEl) statusEl.textContent = "";

      const data = {
        name: form.querySelector('[name="name"]').value,
        email: form.querySelector('[name="email"]').value,
        message: form.querySelector('[name="message"]').value,
        page: form.dataset.contactForm || "general",
      };

      try {
        const resp = await fetch("/api/contact", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });

        const result = await resp.json();

        if (resp.ok) {
          if (statusEl) {
            statusEl.textContent = "Message sent! We'll be in touch soon.";
            statusEl.className = "form-status success";
          }
          form.reset();
        } else {
          if (statusEl) {
            statusEl.textContent =
              result.error || "Something went wrong. Please try again.";
            statusEl.className = "form-status error";
          }
        }
      } catch {
        if (statusEl) {
          statusEl.textContent =
            "Network error. Please check your connection and try again.";
          statusEl.className = "form-status error";
        }
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    });
  });
});
