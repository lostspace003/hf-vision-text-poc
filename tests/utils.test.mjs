import { test } from "node:test";
import assert from "node:assert/strict";
import { validateText, validateImage, isValidSpaceId, pct, sentimentEmoji } from "../web/js/utils.js";

test("validateText", () => {
  assert.equal(validateText("  hi ").value, "hi");
  assert.equal(validateText("").ok, false);
  assert.equal(validateText("a".repeat(5001)).ok, false);
});

test("validateImage", () => {
  assert.equal(validateImage(null).ok, false);
  assert.equal(validateImage({ type: "image/png", size: 100 }).ok, true);
  assert.equal(validateImage({ type: "application/pdf", size: 100 }).ok, false);
  assert.equal(validateImage({ type: "image/png", size: 11 * 1024 * 1024 }).ok, false);
});

test("isValidSpaceId", () => {
  assert.equal(isValidSpaceId("user/vision-text-poc"), true);
  assert.equal(isValidSpaceId("bad"), false);
  assert.equal(isValidSpaceId(""), false);
});

test("formatting", () => {
  assert.equal(pct(0.1234), "12.3%");
  assert.equal(sentimentEmoji("positive"), "😊");
  assert.equal(sentimentEmoji("x"), "❔");
});
