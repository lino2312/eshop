package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type ProductResponse struct {
	Product struct {
		VariationAttributes []struct {
			Values []struct {
				Selectable bool `json:"selectable"`
			} `json:"values"`
		} `json:"variationAttributes"`
	} `json:"product"`
}

func main() {
	url := "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Product-Variation?dwvar_IP17scol_color=25&pid=IP17scol&quantity=1&source=ajax&offerPriceId=hkd-m-Inbase-prices"

	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	startTime := time.Now()

	for i := 0; i < 100; i++ {
		resp, err := client.Get(url)
		if err != nil {
			fmt.Printf("请求失败: %v\n", err)
			continue
		}

		body, err := io.ReadAll(resp.Body)
		resp.Body.Close()
		if err != nil {
			fmt.Printf("读取响应失败: %v\n", err)
			continue
		}

		var result ProductResponse
		if err := json.Unmarshal(body, &result); err != nil {
			fmt.Printf("解析JSON失败: %v\n", err)
			continue
		}

		if len(result.Product.VariationAttributes) < 2 {
			fmt.Println("variationAttributes 数据不足")
			continue
		}

		romBase := result.Product.VariationAttributes[1].Values
		if len(romBase) < 2 {
			fmt.Println("内存选项数据不足")
			continue
		}

		g256 := romBase[0].Selectable
		g512 := romBase[1].Selectable
		fmt.Printf("%v %v\n", g256, g512)

		// time.Sleep(1 * time.Second)
	}

	elapsed := time.Since(startTime)
	fmt.Printf("运行时间: %.2f 秒\n", elapsed.Seconds())
}
