const rupees = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
})

// Display only. Prices arrive as exact decimal strings ("1800.00") and no
// arithmetic happens on the converted number.
export function formatRupees(amount: string): string {
  return rupees.format(Number(amount))
}
