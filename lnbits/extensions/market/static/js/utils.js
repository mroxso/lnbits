function initNostrMarket(data) {
  console.log(data)
  let stalls = data.stalls.map(stall => {
    return {
      id: stall.id,
      name: stall.name,
      description: '',
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
          images: p.image && [
            p.image.startsWith('data:') ? p.image.slice(0, 20) : p.image
          ],
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

function nostrStallData(data, action = 'update') {
  return {
    action,
    stalls: [
      {
        id: data.id,
        name: data.name,
        description: '',
        shipping: data.shippingzones,
        action
      }
    ]
  }
}

function nostrProductData(data, action = 'update') {
  let stallId = data.stall

  return {
    action,
    stalls: [
      {
        id: stallId,
        products: [
          {
            id: data.id,
            name: data.product,
            description: data.description,
            categories: data.categories,
            amount: data.quantity,
            price: data.price,
            images: data.image && [
              data.image.startsWith('data:')
                ? data.image.slice(0, 20)
                : data.image
            ],
            action: null
          }
        ]
      }
    ]
  }
}

async function subscribeToChatRelay(relay, pubkeys) {
  await relay.connect()

  relay.on('connect', () => {
    console.log(`connected to ${relay.url}`)
  })
  relay.on('error', () => {
    console.log(`failed to connect to ${relay.url}`)
  })

  let sub = relay.sub({
    filter: {
      kinds: [4],
      authors: authors,
      '#p': authors
    }
  })

  sub.on('event', event => {
    console.log('we got the event we wanted:', event)
  })

  return sub
}

async function publishNostrEvent(relay, event) {
  //connect to relay
  await relay.connect()

  relay.on('connect', () => {
    console.log(`connected to ${relay.url}`)
  })
  relay.on('error', () => {
    console.log(`failed to connect to ${relay.url}`)
  })
  //publish event
  let pub = relay.publish(event)
  pub.on('ok', () => {
    console.log(`${relay.url} has accepted our event`)
  })
  pub.on('seen', () => {
    console.log(`we saw the event on ${relay.url}`)
    relay.close()
  })
  pub.on('failed', reason => {
    console.log(`failed to publish to ${relay.url}: ${reason}`)
    relay.close()
  })
  return
}
