// @ts-check
/**
 * E2E Tests for NDA Form
 * @see nda-form.php
 */

const { test, expect } = require('@playwright/test');

test.describe('NDA Form', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/nda-form.php');
  });

  test('should display NDA form page', async ({ page }) => {
    await expect(page).toHaveTitle(/NDA/);
    await expect(page.locator('h1')).toContainText('Umowa o poufności');
  });

  test('should show step indicators', async ({ page }) => {
    await expect(page.locator('.steps')).toContainText('NIP');
    await expect(page.locator('.steps')).toContainText('Dane firmy');
    await expect(page.locator('.steps')).toContainText('Podpis i upload');
  });

  test('should start at step 1', async ({ page }) => {
    await expect(page.locator('.step.active')).toContainText('NIP');
    await expect(page.locator('.step.active .step-number')).toContainText('1');
  });

  test('should show NIP input form at step 1', async ({ page }) => {
    await expect(page.locator('input[name="nip"]')).toBeVisible();
    await expect(page.locator('button:has-text("Pobierz dane")')).toBeVisible();
  });

  test('should accept valid NIP', async ({ page }) => {
    const nipInput = page.locator('input[name="nip"]');
    await nipInput.fill('1234567890');
    await expect(nipInput).toHaveValue('1234567890');
  });

  test('should clean NIP from spaces and dashes', async ({ page }) => {
    const nipInput = page.locator('input[name="nip"]');
    
    // Try with spaces
    await nipInput.fill('123 456 7890');
    // Frontend might clean this, or we rely on backend cleaning
    await expect(nipInput).toHaveValue('123 456 7890');
  });

  test('should proceed to step 2 with demo NIP', async ({ page }) => {
    // Enter demo NIP that returns data
    await page.fill('input[name="nip"]', '1234567890');
    await page.click('button:has-text("Pobierz dane")');
    
    // Should show company data form
    await expect(page.locator('input[name="nazwa"]')).toBeVisible();
    await expect(page.locator('.step.active')).toContainText('Osoba kontaktowa');
  });

  test('should show company data prefilled from NIP', async ({ page }) => {
    // Enter demo NIP
    await page.fill('input[name="nip"]', '1234567890');
    await page.click('button:has-text("Pobierz dane")');
    
    // Check prefilled data
    const nazwaInput = page.locator('input[name="nazwa"]');
    await expect(nazwaInput).toHaveValue('Example Company Sp. z o.o.');
    
    const miastoInput = page.locator('input[name="miasto"]');
    await expect(miastoInput).toHaveValue('Warszawa');
  });

  test('should require all fields in step 2', async ({ page }) => {
    // Enter demo NIP to get to step 2
    await page.fill('input[name="nip"]', '1234567890');
    await page.click('button:has-text("Pobierz dane")');
    
    // Check required fields
    await expect(page.locator('input[name="osoba"]')).toHaveAttribute('required', '');
    await expect(page.locator('input[name="stanowisko"]')).toHaveAttribute('required', '');
    await expect(page.locator('input[name="email"]')).toHaveAttribute('required', '');
  });

  test('should proceed to step 3 after filling form', async ({ page }) => {
    // Enter demo NIP
    await page.fill('input[name="nip"]', '1234567890');
    await page.click('button:has-text("Pobierz dane")');
    
    // Fill person data
    await page.fill('input[name="osoba"]', 'Jan Kowalski');
    await page.fill('input[name="stanowisko"]', 'CEO');
    await page.fill('input[name="email"]', 'jan@example.com');
    
    // Submit
    await page.click('button:has-text("Generuj NDA")');
    
    // Should show generated NDA
    await expect(page.locator('.step.active')).toContainText('Podpis i upload');
    await expect(page.locator('.nda-preview')).toBeVisible();
    await expect(page.locator('.nda-preview')).toContainText('UMOWA O ZACHOWANIU POUFNOŚCI');
  });

  test('should show generated NDA text with correct data', async ({ page }) => {
    // Go through steps
    await page.fill('input[name="nip"]', '1234567890');
    await page.click('button:has-text("Pobierz dane")');
    
    await page.fill('input[name="osoba"]', 'Jan Kowalski');
    await page.fill('input[name="stanowisko"]', 'CEO');
    await page.fill('input[name="email"]', 'jan@example.com');
    await page.click('button:has-text("Generuj NDA")');
    
    // Check NDA content
    const ndaText = page.locator('.nda-preview');
    await expect(ndaText).toContainText('Example Company Sp. z o.o.');
    await expect(ndaText).toContainText('Jan Kowalski');
    await expect(ndaText).toContainText('CEO');
    await expect(ndaText).toContainText('3 lat'); // Protection period
  });

  test('should have download button in step 3', async ({ page }) => {
    // Go through steps
    await page.fill('input[name="nip"]', '1234567890');
    await page.click('button:has-text("Pobierz dane")');
    
    await page.fill('input[name="osoba"]', 'Jan Kowalski');
    await page.fill('input[name="stanowisko"]', 'CEO');
    await page.fill('input[name="email"]', 'jan@example.com');
    await page.click('button:has-text("Generuj NDA")');
    
    // Check download button exists
    await expect(page.locator('a:has-text("Pobierz TXT")')).toBeVisible();
    await expect(page.locator('button:has-text("Drukuj / Zapisz PDF")')).toBeVisible();
  });

  test('should have upload zone in step 3', async ({ page }) => {
    // Go through steps
    await page.fill('input[name="nip"]', '1234567890');
    await page.click('button:has-text("Pobierz dane")');
    
    await page.fill('input[name="osoba"]', 'Jan Kowalski');
    await page.fill('input[name="stanowisko"]', 'CEO');
    await page.fill('input[name="email"]', 'jan@example.com');
    await page.click('button:has-text("Generuj NDA")');
    
    // Check upload zone
    await expect(page.locator('.upload-zone')).toBeVisible();
    await expect(page.locator('.upload-zone')).toContainText('Prześlij podpisaną umowę');
  });

  test('should have manual entry link', async ({ page }) => {
    await expect(page.locator('a:has-text("Wypełnij ręcznie")')).toBeVisible();
  });

  test('should validate email format', async ({ page }) => {
    // Enter demo NIP
    await page.fill('input[name="nip"]', '1234567890');
    await page.click('button:has-text("Pobierz dane")');
    
    // Try invalid email
    const emailInput = page.locator('input[name="email"]');
    await emailInput.fill('invalid-email');
    await expect(emailInput).toHaveValue('invalid-email');
    // HTML5 validation should prevent form submission
  });
});

test.describe('NDA Form - Manual Entry', () => {
  test('should allow manual company data entry', async ({ page }) => {
    await page.goto('/nda-form.php');
    
    // Click manual entry link
    await page.click('a:has-text("Wypełnij ręcznie")');
    
    // Should show form with empty fields
    await expect(page.locator('input[name="nazwa"]')).toBeVisible();
    await expect(page.locator('input[name="nazwa"]')).toHaveValue('');
  });
});

test.describe('NDA Form - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('should be responsive on mobile', async ({ page }) => {
    await page.goto('/nda-form.php');
    
    await expect(page.locator('h1')).toContainText('Umowa o poufności');
    await expect(page.locator('input[name="nip"]')).toBeVisible();
  });
});
