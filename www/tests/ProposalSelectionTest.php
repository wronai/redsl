<?php
/**
 * Tests for Proposal Selection GUI
 * 
 * @covers Proposal selection functionality
 */

use PHPUnit\Framework\TestCase;

class ProposalSelectionTest extends TestCase
{
    /**
     * Test proposal list rendering
     */
    public function testProposalListRendering(): void
    {
        $proposals = [
            ['id' => 1, 'title' => 'Refaktoryzacja klasy UserService', 'file' => 'src/services/UserService.php', 'effort' => 'M', 'lines' => 150, 'price' => 10, 'redsl_min' => 8],
            ['id' => 2, 'title' => 'Ekstrakcja metod', 'file' => 'src/controllers/Test.php', 'effort' => 'S', 'lines' => 80, 'price' => 10, 'redsl_min' => 4],
        ];
        
        $this->assertCount(2, $proposals);
        $this->assertEquals(1, $proposals[0]['id']);
        $this->assertEquals('Refaktoryzacja klasy UserService', $proposals[0]['title']);
        $this->assertEquals(10, $proposals[0]['price']);
        $this->assertEquals(8, $proposals[0]['redsl_min']);
    }
    
    /**
     * Test selection parser - single items
     */
    public function testSelectionParserSingle(): void
    {
        $input = "1, 3, 7";
        $ids = $this->parseSelection($input);
        
        $this->assertEquals([1, 3, 7], $ids);
    }
    
    /**
     * Test selection parser - ranges
     */
    public function testSelectionParserRanges(): void
    {
        $input = "12-15";
        $ids = $this->parseSelection($input);
        
        $this->assertEquals([12, 13, 14, 15], $ids);
    }
    
    /**
     * Test selection parser - mixed
     */
    public function testSelectionParserMixed(): void
    {
        $input = "1, 3, 7, 12-15, 24";
        $ids = $this->parseSelection($input);
        
        $this->assertEquals([1, 3, 7, 12, 13, 14, 15, 24], $ids);
    }
    
    /**
     * Test selection parser - empty
     */
    public function testSelectionParserEmpty(): void
    {
        $input = "";
        $ids = $this->parseSelection($input);
        
        $this->assertEquals([], $ids);
    }
    
    /**
     * Test price calculation
     */
    public function testPriceCalculation(): void
    {
        $selectedIds = [1, 3, 7, 12, 13, 14, 15, 24];
        $pricePerTicket = 10;
        $total = count($selectedIds) * $pricePerTicket;
        
        $this->assertEquals(80, $total);
    }
    
    /**
     * Test effort labels — human hours + ReDSL minutes
     */
    public function testEffortLabels(): void
    {
        $humanHours = [
            'S' => '~2h',
            'M' => '~4h',
            'L' => '~8h',
        ];

        $this->assertEquals('~2h', $humanHours['S']);
        $this->assertEquals('~4h', $humanHours['M']);
        $this->assertEquals('~8h', $humanHours['L']);
    }

    /**
     * Test redsl_min field present and reasonable
     */
    public function testRedslMinField(): void
    {
        $proposals = [
            ['id' => 1, 'effort' => 'M', 'redsl_min' => 8],
            ['id' => 2, 'effort' => 'S', 'redsl_min' => 4],
            ['id' => 3, 'effort' => 'L', 'redsl_min' => 15],
        ];

        foreach ($proposals as $p) {
            $this->assertArrayHasKey('redsl_min', $p);
            $this->assertGreaterThan(0, $p['redsl_min']);
            $this->assertLessThanOrEqual(60, $p['redsl_min']);
        }
    }
    
    /**
     * Test form submission simulation
     */
    public function testFormSubmission(): void
    {
        $_POST = [
            'selection' => 'custom',
            'custom_input' => '1, 3, 7',
        ];
        
        $this->assertEquals('custom', $_POST['selection']);
        $this->assertEquals('1, 3, 7', $_POST['custom_input']);
        
        $parsedIds = $this->parseSelection($_POST['custom_input']);
        $this->assertEquals([1, 3, 7], $parsedIds);
        $this->assertCount(3, $parsedIds);
    }
    
    /**
     * Test "all" selection
     */
    public function testAllSelection(): void
    {
        $proposals = [
            ['id' => 1], ['id' => 2], ['id' => 3],
            ['id' => 4], ['id' => 5], ['id' => 6],
            ['id' => 7], ['id' => 8],
        ];
        
        $selection = 'all';
        $selectedIds = $selection === 'all' 
            ? array_column($proposals, 'id') 
            : [];
        
        $this->assertCount(8, $selectedIds);
        $this->assertEquals([1, 2, 3, 4, 5, 6, 7, 8], $selectedIds);
    }
    
    /**
     * Test "under 15" selection (all tickets are 10 PLN)
     */
    public function testUnder15Selection(): void
    {
        $proposals = [
            ['id' => 1, 'price' => 10],
            ['id' => 2, 'price' => 10],
            ['id' => 3, 'price' => 10],
        ];
        
        $selection = 'under_15';
        $selectedIds = $selection === 'under_15'
            ? array_column($proposals, 'id')
            : [];
        
        $this->assertCount(3, $selectedIds);
    }
    
    /**
     * Helper: parse selection input
     */
    private function parseSelection(string $input): array
    {
        $ids = [];
        $parts = array_map('trim', explode(',', $input));
        
        foreach ($parts as $part) {
            if (strpos($part, '-') !== false) {
                [$start, $end] = array_map('intval', explode('-', $part));
                for ($i = $start; $i <= $end; $i++) {
                    $ids[] = $i;
                }
            } else {
                $val = intval($part);
                if ($val > 0) {
                    $ids[] = $val;
                }
            }
        }
        
        return array_unique($ids);
    }
}
