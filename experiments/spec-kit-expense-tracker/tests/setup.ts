import "@testing-library/jest-dom/vitest";

if (
  typeof HTMLDialogElement !== "undefined" &&
  typeof HTMLDialogElement.prototype.showModal !== "function"
) {
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
    configurable: true,
    value(this: HTMLDialogElement) {
      this.setAttribute("open", "");
      this.focus();
    },
  });
  Object.defineProperty(HTMLDialogElement.prototype, "close", {
    configurable: true,
    value(this: HTMLDialogElement, returnValue = "") {
      this.returnValue = returnValue;
      this.removeAttribute("open");
      this.dispatchEvent(new Event("close"));
    },
  });
}
