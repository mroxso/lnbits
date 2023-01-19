async function initNostrMarket(data) {
  console.log(data)
  let stalls = data.stalls.map(stall => {
    return {
      id: stall.id,
      name: stall.name,
      description: '',
      categories: [],
      shipping: stall.shippingzones,
      products: data.products
        .filter(p => p.stall === stall.id)
        .map(p => ({
          id: p.id,
          name: p.product,
          description: p.description,
          categories: p.categories,
          amount: p.quantity,
          price: p.price,
          image: p.image.startsWith('data:') ? p.image.slice(0, 20) : p.image,
          action: null
        })),
      action: null
    }
  })
  return {
    name: '',
    description: '',
    currency: '',
    action: null,
    stalls
  }
}
